# Data scripts

## News (automated after deploy)

Production path: **NHSRCL press listing → Django `NewsArticle` → rewrite + dedupe**. No manual JSON edits required.

### One-shot (cron / deploy)

```bash
bash scripts/sync-news.sh
bash scripts/sync-news.sh --backfill-json   # also seed from data/updates.json if DB has fewer than 12 articles
```

### Lightsail timer (recommended)

```bash
sudo BTS_INSTALL_ROOT=/opt/bullettrainstation bash scripts/install-news-timer.sh
# or during bootstrap:
sudo BTS_INSTALL_NEWS_TIMER=1 bash scripts/lightsail-backend-bootstrap.sh
```

Runs `sync_news` every **15 minutes** via `bts-news-sync.timer`.

### Long-running watcher (dev or supervisor)

```bash
npm run watch-developments
bash scripts/news-watcher.sh --once   # single poll
bash scripts/news-watcher.sh --interval 600 --export-json
```

Each poll: NHSRCL fetch, `reprocess_articles`, `prune_duplicate_articles`, optional `data/updates.json` export for the Next.js fallback.

### Local full bootstrap

```bash
npm run sync-data          # import_catalog + sync_news --backfill-json
npm run api:sync-news      # NHSRCL only (same as cron)
```

Django: `python manage.py sync_news`

## Places

Hotels, cabs, and other listings are **not** auto-loaded in production bootstrap. Seed kinds with `seed_place_kinds`, then add rows in Django admin.

Dev illustrative POIs: `npm run api:sync-places` (optional).

## Refresh DB (catalog + news)

```bash
bash scripts/feed-database.sh
BTS_IMPORT_PLACES=1 bash scripts/feed-database.sh
```

Lightsail: from `~/bullettrainbackend` after bootstrap.

## npm shortcuts

```bash
npm run sync-data
npm run api:sync-news
npm run api:feed-database
npm run watch-developments
```