# Growth News → Discord Bot

Posts US-based growth hacking news to a Discord channel daily at 09:00 KST.

## Sources (default)
- Andrew Chen — https://andrewchen.com/feed/
- Lenny's Newsletter — https://www.lennysnewsletter.com/feed
- Neil Patel — https://neilpatel.com/blog/feed/
- Backlinko (Brian Dean) — https://backlinko.com/feed
- Growth Marketing Pro — https://www.growthmarketingpro.com/feed/
- Nir & Far (Nir Eyal) — https://www.nirandfar.com/feed/
- Optional X via Nitter (Andrew Chen) — set `NITTER_BASE`
- Sean Ellis is intentionally excluded.

You can override the list with `config/growth_news_sources.yml`.

## How to enable
1) Create a Discord webhook for your growth channel
2) In GitHub → repo Settings → Secrets and variables → Actions → New repository secret
   - Name: `GROWTH_WEBHOOK_URL`
   - Value: your growth Discord webhook URL
3) (Optional) Translation to Korean: set `TRANSLATE_TO=ko` and choose a backend (see Agile bot docs)
4) The scheduled workflow `.github/workflows/growth-news.yml` runs daily 09:00 KST (00:00 UTC)

## Advanced
- Freshness window: `POST_WINDOW_HOURS` (default 72h)
- Daily count: `DAILY_COUNT` (default 3), per-source cap `MAX_PER_SOURCE` (default 1)
- Per-feed fetch limit: `PER_FEED_LIMIT` (default 5)
- Cache: `.cache/growth_news_bot.json` persisted via Actions cache

