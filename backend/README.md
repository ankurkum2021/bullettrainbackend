# Bullet Train Station — Django API & admin

Stores corridor entities and news articles. The Next.js site loads updates from this API when `BTS_API_URL` is set (see repo `.env.example`).

## Setup

From the repo root (local dev):

```bash
npm run api:setup
```

### Lightsail / VPS — one script, real data only

```bash
bash scripts/lightsail-backend-bootstrap.sh
# or: npm run api:deploy-bootstrap
```

Loads **corridors**, runs **`sync_news`** (NHSRCL press feed + rewrite + dedupe; one-time JSON backfill if the DB is sparse). **Places** are admin-only unless you set `BTS_RESET_PLACES=1`.

After deploy, install the news timer: `sudo bash scripts/install-news-timer.sh` (every 15 minutes).

`BTS_SKIP_NHSRCL=1` if the server has no outbound HTTPS to NHSRCL on first boot.

Or manually:

```bash
cd backend
python3 -m venv env
./env/bin/pip install -r requirements.txt
./env/bin/python manage.py migrate
python manage.py createsuperuser
python manage.py import_catalog
python manage.py sync_news --backfill-json
python manage.py runserver 8000
```

- Admin: http://127.0.0.1:8000/admin/
- Health: http://127.0.0.1:8000/api/health/
- News API: http://127.0.0.1:8000/api/news/
- Stations: http://127.0.0.1:8000/api/stations/
- Corridors: http://127.0.0.1:8000/api/corridors/

## Apps

| App | Models |
|-----|--------|
| `catalog` | `Corridor`, `Station` |
| `news` | `NewsArticle` |
| `places` | `PlaceKind`, `PlaceSection`, `Place` |

### Places (generic local listings)

Not “Hotel” / “Cab” tables — one **`Place`** model with a **`PlaceKind`** taxonomy (transport, lodging, industry, …) and optional **`PlaceSection`** panels per station.

```bash
python manage.py seed_place_kinds
```

API:

- `GET /api/place-kinds/`
- `GET /api/places/?station=surat&kind=transport`
- `GET /api/stations/surat/places/` — grouped panels for explore UI

## Next.js

Copy `.env.example` to `.env.local` and run both processes:

```bash
npm run api:dev    # :8000
npm run dev        # Next (often :3000)
```

Home and `/updates` call `loadCorridorUpdates()` server-side with ISR (`revalidate=300`). If the API is down, they fall back to `data/updates.json`.

## Developments pipeline (automated)

| Command | Purpose |
|---------|---------|
| `python manage.py sync_news` | NHSRCL fetch, rewrite, dedupe (**use in cron/systemd**) |
| `python manage.py sync_news --backfill-json` | Above + seed from `data/updates.json` if DB has few rows |
| `python manage.py watch_developments` | Long-running poller (same steps each interval) |

Production: `deploy/systemd/bts-news-sync.timer` via `scripts/install-news-timer.sh`.

Repo: `bash scripts/sync-news.sh`, `npm run api:sync-news`, `npm run watch-developments`.

Dedupe uses `source_fingerprint` (SHA-256 of `source_url`). `--export-json` refreshes `data/updates.json` for the Next.js fallback when the API is down.