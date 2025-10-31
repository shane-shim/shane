#!/usr/bin/env python3
"""
Agile News → Discord Webhook

Posts recent Agile/Scrum news items to a Discord webhook.
- Uses public RSS/Atom feeds and optional Nitter RSS for X/Twitter users.
- De-duplicates implicitly by posting only fresh items within a time window.

Environment:
- DISCORD_WEBHOOK_URL (required)
- NITTER_BASE (optional, e.g., https://nitter.net)
- POST_WINDOW_HOURS (optional, default=12) — skip items older than this

Config (optional):
- config/agile_news_sources.yml — list of { name, url } to extend/override defaults

Dependencies: feedparser, pyyaml (optional for config)
"""
from __future__ import annotations

import os
import sys
import json
import time
import urllib.request
from typing import List, Tuple, Optional, Set, Dict, Any
import urllib.parse
import random

try:
    import feedparser  # type: ignore
except Exception:
    print("Missing dependency: feedparser. Install with `pip install feedparser`.", file=sys.stderr)
    sys.exit(2)

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # optional


def get_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        print(f"Missing required env: {name}", file=sys.stderr)
        sys.exit(2)
    return val


def default_sources() -> List[Tuple[str, str]]:
    sources: List[Tuple[str, str]] = [
        ("Scrum.org", "https://www.scrum.org/resources/rss.xml"),
        ("InfoQ Agile", "https://www.infoq.com/agile/rss/"),
        ("Martin Fowler", "https://martinfowler.com/feed.atom"),
        ("Scrum Alliance", "https://resources.scrumalliance.org/feed"),
        ("Agile Alliance", "https://www.agilealliance.org/feed/"),
        ("Mike Cohn (Mountain Goat)", "https://www.mountaingoatsoftware.com/blog/rss"),
        ("Kanban University", "https://kanban.university/blog/feed/"),
        ("r/agile", "https://www.reddit.com/r/agile/.rss"),
        ("r/scrum", "https://www.reddit.com/r/scrum/.rss"),
    ]
    nitter = os.environ.get("NITTER_BASE", "").strip()
    if nitter:
        # Jeff Sutherland & Ken Schwaber via Nitter RSS (if available)
        sources.append(("Jeff Sutherland (X)", f"{nitter.rstrip('/')}/jeffsutherland/rss"))
        sources.append(("Ken Schwaber (X)", f"{nitter.rstrip('/')}/kschwaber/rss"))
    return sources


def load_sources_from_yaml(path: str) -> Optional[List[Tuple[str, str]]]:
    if yaml is None:
        return None
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        result: List[Tuple[str, str]] = []
        for item in data:
            name = str(item.get("name", "")).strip()
            url = str(item.get("url", "")).strip()
            if name and url:
                result.append((name, url))
        return result or None
    except Exception as e:
        print(f"[WARN] Failed to read YAML sources: {e}", file=sys.stderr)
        return None


def fetch_feed(url: str):
    return feedparser.parse(url)


def post_discord(webhook: str, content: str, *, title: Optional[str] = None, url: Optional[str] = None, footer: Optional[str] = None) -> None:
    use_embeds = os.environ.get("DISCORD_USE_EMBEDS", "0") in ("1", "true", "True")
    payload: Dict[str, Any]
    if use_embeds and (title or url):
        embed: Dict[str, Any] = {
            "type": "rich",
            "title": title or "Agile News",
            "url": url or None,
            "description": content,
        }
        if footer:
            embed["footer"] = {"text": footer}
        payload = {"embeds": [embed]}
    else:
        payload = {"content": content}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"Discord responded with {resp.status}")


def _fields(entry) -> Tuple[str, str, str, str]:
    title = getattr(entry, "title", "(no title)")
    link = getattr(entry, "link", "")
    published = getattr(entry, "published", "") or getattr(entry, "updated", "")
    summary = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""
    return title, link, published, summary


def build_message(source: str, entry, translate_to: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
    title, link, published, summary = _fields(entry)
    # content body (for non-embed fallback)
    msg = f"[{source}] {title}\n{link}"
    if published:
        msg += f"\nPublished: {published}"
    trans = None
    if translate_to:
        compact = _ensure_len(f"{title}\n{summary}", 800)
        tr = translate_text(compact, translate_to)
        if tr:
            trans = _ensure_len(tr, 900)
            msg += f"\n\n[번역]\n{trans}"
    return _ensure_len(msg, 1900), title, published or None


def entry_age_hours(entry) -> Optional[float]:
    # Use published_parsed or updated_parsed if available
    ts = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not ts:
        return None


# --- Translation helpers (optional backends) ---

def _ensure_len(s: str, limit: int = 1800) -> str:
    if len(s) <= limit:
        return s
    return s[: limit - 3] + "..."


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
        body = {
            "q": text,
            "source": "auto",
            "target": target,
            "format": "text",
        }
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
            tr = payload.get("translatedText") or payload.get("translation")
            return tr
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
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
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
    # Try backends in order of env preference
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
    # Fallback auto-pick
    for fn in (_translate_deepl, _translate_libre, _translate_openai):
        tr = fn(text, target)
        if tr:
            return tr
    return None


def load_cache(path: str) -> Set[str]:
    try:
        if not os.path.exists(path):
            return set()
        with open(path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
        links = set(data.get("links", []))
        return links
    except Exception:
        return set()


def save_cache(path: str, links: Set[str]) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"links": sorted(links)}, f)
    except Exception as e:
        print(f"[WARN] Failed to save cache: {e}", file=sys.stderr)
    # time.struct_time → epoch
    try:
        epoch = time.mktime(ts)
        return (time.time() - epoch) / 3600.0
    except Exception:
        return None


def main() -> None:
    webhook = get_env("DISCORD_WEBHOOK_URL")
    sources = default_sources()
    # Merge/override via YAML config
    user_sources = load_sources_from_yaml("config/agile_news_sources.yml")
    if user_sources:
        sources = user_sources

    window_hours = float(os.environ.get("POST_WINDOW_HOURS", "12"))
    cache_path = os.environ.get("CACHE_PATH", ".cache/agile_news_bot.json")
    cache_links = load_cache(cache_path)
    translate_to = os.environ.get("TRANSLATE_TO", "").strip() or None

    seen_links = set()
    # Collect candidates across sources
    per_feed_limit = int(os.environ.get("PER_FEED_LIMIT", "5"))
    candidates: List[Tuple[float, str, Any]] = []  # (epoch, source, entry)
    for source, url in sources:
        try:
            feed = fetch_feed(url)
            if getattr(feed, 'bozo', False):
                continue
            entries = getattr(feed, 'entries', []) or []
            for entry in entries[:per_feed_limit]:
                link = getattr(entry, "link", "")
                if not link:
                    continue
                if link in seen_links or link in cache_links:
                    continue
                age = entry_age_hours(entry)
                if age is not None and age > window_hours:
                    continue
                ts = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
                epoch = time.mktime(ts) if ts else time.time()
                candidates.append((epoch, source, entry))
        except Exception as e:
            print(f"[WARN] Fetch {source}: {e}", file=sys.stderr)
            continue

    if not candidates:
        # Post a heartbeat so it's visible that the bot ran
        try:
            post_discord(
                webhook,
                f"[Agile News Bot] 최근 {int(window_hours)}시간 동안 새 항목이 없습니다.",
                title="Agile News Bot",
                url=None,
                footer="heartbeat"
            )
        except Exception as e:
            print(f"[WARN] Heartbeat post failed: {e}", file=sys.stderr)
        save_cache(cache_path, cache_links)
        return

    # Random selection with per-source cap
    daily_count = int(os.environ.get("DAILY_COUNT", "3"))
    max_per_source = int(os.environ.get("MAX_PER_SOURCE", "1"))

    random.shuffle(candidates)
    selected: List[Tuple[float, str, Any]] = []
    used_per_source: Dict[str, int] = {}
    for epoch, source, entry in candidates:
        if len(selected) >= daily_count:
            break
        if used_per_source.get(source, 0) >= max_per_source:
            continue
        selected.append((epoch, source, entry))
        used_per_source[source] = used_per_source.get(source, 0) + 1

    # Post selected items (sorted by recency ascending to preserve order)
    for _, source, entry in sorted(selected, key=lambda x: -x[0]):
        link = getattr(entry, "link", "")
        if not link:
            continue
        cache_links.add(link)
        msg, title, published = build_message(source, entry, translate_to)
        try:
            post_discord(webhook, msg, title=title, url=getattr(entry, "link", ""), footer=(f"{source} • {published}" if published else source))
        except Exception as e:
            print(f"[WARN] Discord post failed: {e}", file=sys.stderr)
        time.sleep(1.2)

    save_cache(cache_path, cache_links)


if __name__ == "__main__":
    main()
