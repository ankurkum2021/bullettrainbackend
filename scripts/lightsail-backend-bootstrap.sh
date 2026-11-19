#!/usr/bin/env bash
#
# Single Lightsail (or VPS) bootstrap: venv, migrations, automated news, catalog.
#
# News runs without manual steps after deploy — enable the systemd timer
#   sudo BTS_INSTALL_ROOT=/path/to/repo bash scripts/install-news-timer.sh
#
# Places (hotels, cabs, etc.) are yours via Django admin; bootstrap only seeds
# PlaceKind taxonomy unless BTS_RESET_PLACES=1.
#
# Usage (on server, from repo root):
#   bash scripts/lightsail-backend-bootstrap.sh
#
# Env (optional):
#   BTS_SKIP_NHSRCL=1       Skip live NHSRCL fetch (offline / CI)
#   BTS_RESET_PLACES=1      clear_place_listings + import data/places-realistic.json
#   BTS_INSTALL_NEWS_TIMER=1  Run install-news-timer.sh when root/sudo
#   BTS_PYTHON=python3.12   Override python for venv creation
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
VENV="$BACKEND/env"
PY_BIN="${BTS_PYTHON:-python3}"
DJANGO_PY="$VENV/bin/python"

run_manage() {
  (cd "$BACKEND" && "$DJANGO_PY" manage.py "$@")
}

echo "==> Bullet Train Station backend bootstrap"
echo "    Root: $ROOT"

if [[ ! -f "$BACKEND/requirements.txt" ]]; then
  echo "Missing backend/requirements.txt" >&2
  exit 1
fi

if [[ ! -d "$VENV" ]]; then
  echo "==> Creating venv ($PY_BIN)"
  "$PY_BIN" -m venv "$VENV"
fi

echo "==> Installing Python dependencies"
"$VENV/bin/pip" install -q -r "$BACKEND/requirements.txt"

echo "==> Django migrate"
run_manage migrate --noinput

echo "==> Place taxonomy (listings via admin / your import)"
run_manage seed_place_kinds
if [[ "${BTS_RESET_PLACES:-0}" == "1" ]]; then
  run_manage clear_place_listings
  if [[ -f "$ROOT/data/places-realistic.json" ]]; then
    run_manage import_places_seed
  fi
fi

echo "==> Corridor + station catalog"
run_manage import_catalog

echo "==> Automated news (JSON backfill if DB sparse + NHSRCL + rewrite + dedupe)"
SYNC_ARGS=(sync_news --backfill-json)
if [[ "${BTS_SKIP_NHSRCL:-0}" == "1" ]]; then
  SYNC_ARGS+=(--skip-nhsrcl)
fi
run_manage "${SYNC_ARGS[@]}"

if [[ "${BTS_INSTALL_NEWS_TIMER:-0}" == "1" ]]; then
  if [[ "$(id -u)" -eq 0 ]]; then
  BTS_INSTALL_ROOT="$ROOT" bash "$ROOT/scripts/install-news-timer.sh"
  else
    echo "Tip: sudo BTS_INSTALL_NEWS_TIMER=1 bash scripts/lightsail-backend-bootstrap.sh" >&2
  fi
fi

echo ""
echo "Done."
echo "  • News: sync_news every 15m — sudo bash scripts/install-news-timer.sh"
echo "  • Catalog: corridors-catalog.json"
echo "  • Places: add in Django admin (kinds already seeded)"
echo ""
echo "Next on Lightsail:"
echo "  1. Set SECRET_KEY, ALLOWED_HOSTS, CORS in backend/.env"
echo "  2. API: $VENV/bin/gunicorn config.wsgi:application -b 0.0.0.0:8000"
echo "  3. Point Next.js BTS_API_URL at this host"
echo ""
echo "Manual news sync: bash scripts/sync-news.sh"