#!/usr/bin/env python3
"""
Growth News → Discord Webhook (Daily random 3)

Posts valuable growth-hacking news to a Discord webhook.
- Pulls multiple public RSS/Atom feeds (US-based growth leaders; excludes Sean Ellis).
- Randomly selects DAILY_COUNT items within POST_WINDOW_HOURS.
- Supports optional Korean translation (same envs as agile bot).

Env (common):
- DISCORD_WEBHOOK_URL (required)
- POST_WINDOW_HOURS (default 72)
- DAILY_COUNT (default 3), MAX_PER_SOURCE (default 1), PER_FEED_LIMIT (default 5)
- TRANSLATE_TO, TRANSLATE_BACKEND, DEEPL_API_KEY, LIBRETRANSLATE_URL, LIBRETRANSLATE_API_KEY,
  OPENAI_API_KEY, OPENAI_MODEL
- NITTER_BASE (optional) for X/Twitter via Nitter

Optional config file overrides defaults: config/growth_news_sources.yml

Dependencies: feedparser, pyyaml(optional)
"""
from __future__ import annotations

import os, sys, json, time, random
import urllib.request, urllib.parse, urllib.error
import subprocess
from typing import List, Tuple, Optional, Set, Dict, Any

try:
    import feedparser  # type: ignore
except Exception:
    print("Missing dependency: feedparser. Install with `pip install feedparser`.", file=sys.stderr)
    sys.exit(2)

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def get_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        print(f"Missing required env: {name}", file=sys.stderr)
        sys.exit(2)
    return val


def default_sources() -> List[Tuple[str, str]]:
    sources: List[Tuple[str, str]] = [
        ("Andrew Chen", "https://andrewchen.com/feed/"),
        ("Lenny's Newsletter", "https://www.lennysnewsletter.com/feed"),
        ("Neil Patel", "https://neilpatel.com/blog/feed/"),
        ("Backlinko (Brian Dean)", "https://backlinko.com/feed"),
        ("Growth Marketing Pro", "https://www.growthmarketingpro.com/feed/"),
        ("Nir & Far (Nir Eyal)", "https://www.nirandfar.com/feed/"),
    ]
    nitter = os.environ.get("NITTER_BASE", "").strip()
    if nitter:
        sources.append(("Andrew Chen (X)", f"{nitter.rstrip('/')}/andrewchen/rss"))
        sources.append(("Sean Ellis (X)", f"{nitter.rstrip('/')}/SeanEllis/rss"))
    return sources


def load_sources_from_yaml(path: str) -> Optional[List[Tuple[str, str]]]:
    if yaml is None or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        out: List[Tuple[str, str]] = []
        for item in data:
            name = str(item.get("name", "")).strip()
            url = str(item.get("url", "")).strip()
            if name and url:
                out.append((name, url))
        return out or None
    except Exception as e:
        print(f"[WARN] YAML sources error: {e}", file=sys.stderr)
        return None


def fetch_feed(url: str):
    headers = {
        "User-Agent": "NerdlabNewsBot/1.0 (+https://nerdlab.local)",
        "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
    }
    try:
        feed = feedparser.parse(url, request_headers=headers)
        if getattr(feed, 'entries', None):
            return feed
    except Exception:
        pass
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
        return feedparser.parse(content)
    except Exception:
        return feedparser.parse("")


def post_discord(webhook: str, content: str) -> None:
    """Post message to Discord with urllib -> curl fallback.

    Controlled by envs:
    - DISCORD_USE_CURL: if truthy, use curl directly
    - STRICT_DISCORD: if truthy, raise on non-2xx
    """
    thread_id = os.environ.get("DISCORD_THREAD_ID", "").strip()
    url = webhook
    url += ("&" if "?" in url else "?") + "wait=true"
    if thread_id:
        url += f"&thread_id={urllib.parse.quote(thread_id)}"

    payload = json.dumps({"content": content})
    strict = os.environ.get("STRICT_DISCORD", "").lower() not in ("", "0", "false", "no")
    force_curl = os.environ.get("DISCORD_USE_CURL", "").lower() not in ("", "0", "false", "no")

    def _curl_send() -> None:
        try:
            proc = subprocess.run(
                [
                    "curl",
                    "-sS",
                    "-i",
                    "-H",
                    "Content-Type: application/json",
                    "-H",
                    "User-Agent: NerdlabNewsBot/1.0 (+https://nerdlab.local)",
                    "-X",
                    "POST",
                    url,
                    "--data",
                    payload,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            status_code = 0
            for line in proc.stdout.splitlines():
                if line.startswith("HTTP/"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        status_code = int(parts[1])
                    break
            if status_code and status_code < 300:
                print(f"[INFO] curl Discord post OK: HTTP {status_code}")
            else:
                msg = f"[ERROR] curl Discord post failed: HTTP {status_code or 'unknown'}"
                print(msg, file=sys.stderr)
                if strict:
                    raise RuntimeError(msg)
        except Exception as e:
            print(f"[ERROR] curl post error: {e}", file=sys.stderr)
            if strict:
                raise

    if force_curl:
        _curl_send()
        return

    # urllib path first
    data = payload.encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "NerdlabNewsBot/1.0 (+https://nerdlab.local)",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status >= 300:
                body = resp.read().decode("utf-8", errors="ignore")
                err = f"Discord responded with {resp.status}: {body}"
                print(f"[ERROR] {err}", file=sys.stderr)
                if strict:
                    raise RuntimeError(err)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"[WARN] urllib HTTPError {e.code}: {body}", file=sys.stderr)
        _curl_send()
    except urllib.error.URLError as e:
        print(f"[WARN] urllib URLError: {e.reason}", file=sys.stderr)
        _curl_send()


def _ensure_len(s: str, limit: int = 1900) -> str:
    return s if len(s) <= limit else s[: limit - 3] + "..."


def build_message(source: str, entry, translate_to: Optional[str]) -> str:
    title = getattr(entry, "title", "(no title)")
    link = getattr(entry, "link", "")
    published = getattr(entry, "published", "") or getattr(entry, "updated", "")
    msg = f"[{source}] {title}\n{link}"
    if published:
        msg += f"\nPublished: {published}"
    # Optional translation
    if translate_to:
        summary = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""
        compact = _ensure_len(f"{title}\n{summary}", 800)
        tr = translate_text(compact, translate_to)
        if tr:
            msg += f"\n\n[번역]\n{_ensure_len(tr, 900)}"
    return _ensure_len(msg, 1900)


def entry_age_hours(entry) -> Optional[float]:
    ts = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not ts:
        return None
    try:
        epoch = time.mktime(ts)
        return (time.time() - epoch) / 3600.0
    except Exception:
        return None


def load_cache(path: str) -> Set[str]:
    try:
        if not os.path.exists(path):
            return set()
        with open(path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
        return set(data.get("links", []))
    except Exception:
        return set()


def save_cache(path: str, links: Set[str]) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"links": sorted(links)}, f)
    except Exception as e:
        print(f"[WARN] Cache save failed: {e}", file=sys.stderr)


# Translation (reuse from agile bot by minimal inline impl)
def _translate_deepl(text: str, target: str) -> Optional[str]:
    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        return None
    for base in ("https://api.deepl.com", "https://api-free.deepl.com"):
        try:
            data = urllib.parse.urlencode({
                "auth_key": api_key,
                "text": text,
                "target_lang": target.upper(),
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/v2/translate",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                tr = payload.get("translations", [{}])[0].get("text")
                if tr:
                    return tr
        except Exception:
            continue
    return None


def _translate_libre(text: str, target: str) -> Optional[str]:
    base = os.environ.get("LIBRETRANSLATE_URL")
    if not base:
        return None
    api_key = os.environ.get("LIBRETRANSLATE_API_KEY", "")
    try:
        body = {"q": text, "source": "auto", "target": target, "format": "text"}
        if api_key:
            body["api_key"] = api_key
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            base.rstrip("/") + "/translate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return payload.get("translatedText") or payload.get("translation")
    except Exception:
        return None


def _translate_openai(text: str, target: str) -> Optional[str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are a translator. Translate user text into {target} (Korean). Keep it concise and preserve URLs."},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            base.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            choices = payload.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content")
    except Exception:
        return None
    return None


def translate_text(text: str, target: Optional[str]) -> Optional[str]:
    if not target:
        return None
    target = target.lower()
    backend = os.environ.get("TRANSLATE_BACKEND", "").lower()
    if backend == "deepl":
        tr = _translate_deepl(text, target)
        if tr:
            return tr
    elif backend == "libre":
        tr = _translate_libre(text, target)
        if tr:
            return tr
    elif backend == "openai":
        tr = _translate_openai(text, target)
        if tr:
            return tr
    for fn in (_translate_deepl, _translate_libre, _translate_openai):
        tr = fn(text, target)
        if tr:
            return tr
    return None


def main() -> None:
    webhook = get_env("DISCORD_WEBHOOK_URL")
    sources = default_sources()
    user_sources = load_sources_from_yaml("config/growth_news_sources.yml")
    if user_sources:
        sources = user_sources

    window_hours = float(os.environ.get("POST_WINDOW_HOURS", "72"))
    cache_path = os.environ.get("CACHE_PATH", ".cache/growth_news_bot.json")
    disable_cache = os.environ.get("DISABLE_CACHE", "") or os.environ.get("BYPASS_CACHE", "")
    cache_links = set() if disable_cache else load_cache(cache_path)
    translate_to = os.environ.get("TRANSLATE_TO", "").strip() or None

    # Collect candidates
    per_feed_limit = int(os.environ.get("PER_FEED_LIMIT", "5"))
    candidates: List[Tuple[float, str, Any]] = []
    seen: Set[str] = set()
    for source, url in sources:
        try:
            feed = fetch_feed(url)
            if getattr(feed, 'bozo', False):
                continue
            for entry in (getattr(feed, 'entries', []) or [])[:per_feed_limit]:
                link = getattr(entry, "link", "")
                if not link or link in seen or link in cache_links:
                    continue
                age = entry_age_hours(entry)
                if age is not None and age > window_hours:
                    continue
                ts = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
                epoch = time.mktime(ts) if ts else time.time()
                candidates.append((epoch, source, entry))
                seen.add(link)
        except Exception as e:
            print(f"[WARN] Fetch {source}: {e}", file=sys.stderr)
            continue

    if not candidates:
        # Relax the time window: include entries ignoring age constraint
        try:
            for source, url in sources:
                try:
                    feed = fetch_feed(url)
                    for entry in (getattr(feed, 'entries', []) or [])[:per_feed_limit]:
                        link = getattr(entry, "link", "")
                        if not link:
                            continue
                        if link in cache_links:
                            continue
                        ts = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
                        epoch = time.mktime(ts) if ts else time.time()
                        candidates.append((epoch, source, entry))
                except Exception:
                    continue
        except Exception:
            pass
        if not candidates:
            if not disable_cache:
                save_cache(cache_path, cache_links)
            return

    daily_count = int(os.environ.get("DAILY_COUNT", "3"))
    max_per_source = int(os.environ.get("MAX_PER_SOURCE", "1"))
    random.shuffle(candidates)
    selected: List[Tuple[float, str, Any]] = []
    used: Dict[str, int] = {}
    for epoch, source, entry in candidates:
        if len(selected) >= daily_count:
            break
        if used.get(source, 0) >= max_per_source:
            continue
        selected.append((epoch, source, entry))
        used[source] = used.get(source, 0) + 1

    for _, source, entry in sorted(selected, key=lambda x: -x[0]):
        link = getattr(entry, "link", "")
        if not link:
            continue
        cache_links.add(link)
        msg = build_message(source, entry, translate_to)
        try:
            post_discord(webhook, msg)
        except Exception as e:
            print(f"[WARN] Discord post failed: {e}", file=sys.stderr)
        time.sleep(1.2)

    if not disable_cache:
        save_cache(cache_path, cache_links)


if __name__ == "__main__":
    main()
