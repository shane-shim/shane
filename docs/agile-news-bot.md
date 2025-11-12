# Agile News → Discord Bot

Posts worldwide Agile news to a Discord channel via webhook.

## What it does
- Pulls the latest item from curated sources:
  - Scrum.org blog (`https://www.scrum.org/resources/rss.xml`)
  - InfoQ Agile (`https://www.infoq.com/agile/rss/`)
  - Martin Fowler (`https://martinfowler.com/feed.atom`)
- Optional X/Twitter via Nitter (if you provide a Nitter base):
  - Jeff Sutherland: `<NITTER_BASE>/jeffsutherland/rss`
  - Ken Schwaber: `<NITTER_BASE>/kschwaber/rss`

## How to enable
1) Create a Discord webhook (Server → Channel → Integrations → Webhooks)
2) In GitHub repo settings → Secrets and variables → Actions → New repository secret:
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: your Discord webhook URL
3) (Optional) Add `NITTER_BASE` as a secret, e.g., `https://nitter.net`
4) The scheduled workflow `.github/workflows/agile-news.yml` runs daily at 09:00 KST (00:00 UTC) and on manual dispatch.

### Optional: Korean translation
- Set `TRANSLATE_TO=ko`
- Choose a backend via env/secrets:
  - DeepL: `TRANSLATE_BACKEND=deepl` and add `DEEPL_API_KEY`
  - LibreTranslate: `TRANSLATE_BACKEND=libre` and add `LIBRETRANSLATE_URL` (and optional `LIBRETRANSLATE_API_KEY`)
  - OpenAI: `TRANSLATE_BACKEND=openai` and add `OPENAI_API_KEY` (optional `OPENAI_MODEL`, default `gpt-4o-mini`)

Notes:
- The bot appends a `[번역]` section below the original title/link.
- Message length is truncated to fit Discord limits.

## Local run (optional)
```
pip install feedparser
DISCORD_WEBHOOK_URL=... NITTER_BASE=https://nitter.net \
python scripts/python/agile_news_bot.py
```

## Notes
- Without official X/Twitter API keys, Nitter RSS is a best-effort approach and may be rate-limited or unavailable.
- To reduce duplicates, the bot posts only the most recent item per source each run.
- You can extend sources by editing `scripts/python/agile_news_bot.py`.

## Advanced
- Freshness window: `POST_WINDOW_HOURS` (default 12h; example sets 72h for more candidates)
- Daily count: `DAILY_COUNT` (default 3)
- Per-source cap: `MAX_PER_SOURCE` (default 1)
- Per-feed fetch limit: `PER_FEED_LIMIT` (default 5)
- Cache for de-dup: `.cache/agile_news_bot.json` is persisted via Actions cache
- Custom sources: `config/agile_news_sources.yml` overrides default list (name/url pairs)
