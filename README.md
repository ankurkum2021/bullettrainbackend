# bullettrainbackend

Django API for [bullettrainstation.com](https://bullettrainstation.com): corridors, stations, news (NHSRCL sync), and place listings.

## Layout

| Path | Purpose |
|------|---------|
| `backend/` | Django project (`config`, `catalog`, `news`, `places`) |
| `data/` | JSON seeds (`corridors-catalog.json`, `updates.json`, …) |
| `scripts/` | `django-manage.sh`, Lightsail bootstrap, `sync_news` cron |
| `deploy/systemd/` | News sync timer |

## Quick start

```bash
python3 -m venv backend/env
backend/env/bin/pip install -r backend/requirements.txt
backend/env/bin/python backend/manage.py migrate
bash scripts/django-manage.sh sync_news --backfill-json
bash scripts/django-manage.sh runserver 8000
```

Production bootstrap: `bash scripts/lightsail-backend-bootstrap.sh`

See `backend/README.md` and `scripts/README.md`.