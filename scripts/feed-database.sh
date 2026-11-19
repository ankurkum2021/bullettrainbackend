#!/usr/bin/env bash
#
# Load / refresh Django data: catalog, news, optional places — no venv setup.
# Run from repo root (bullettrainbackend layout: backend/ + data/ + scripts/).
#
# Usage:
#   bash scripts/feed-database.sh
#   BTS_SKIP_NHSRCL=1 bash scripts/feed-database.sh
#   BTS_IMPORT_PLACES=1 bash scripts/feed-database.sh   # illustrative POIs from JSON
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
VENV="$BACKEND/env"
DJANGO_PY="$VENV/bin/python"

if [[ ! -x "$DJANGO_PY" ]]; then
  echo "Missing $VENV — run: bash scripts/lightsail-backend-bootstrap.sh (or npm run api:setup)" >&2
  exit 1
fi

run_manage() {
  (cd "$BACKEND" && "$DJANGO_PY" manage.py "$@")
}

echo "==> feed-database"
echo "    Root: $ROOT"

run_manage migrate --noinput

echo "==> Place kinds"
run_manage seed_place_kinds

if [[ "${BTS_IMPORT_PLACES:-0}" == "1" ]]; then
  if [[ -f "$ROOT/data/places-realistic.json" ]]; then
    echo "==> Places (import JSON; does not clear existing unless BTS_RESET_PLACES=1)"
    if [[ "${BTS_RESET_PLACES:-0}" == "1" ]]; then
      run_manage clear_place_listings
    fi
    run_manage import_places_seed
  else
    echo "WARNING: data/places-realistic.json missing — skip places" >&2
  fi
fi

echo "==> Corridors + stations"
run_manage import_catalog

echo "==> News (JSON backfill + NHSRCL + rewrite + dedupe)"
SYNC_ARGS=(sync_news --backfill-json)
if [[ "${BTS_SKIP_NHSRCL:-0}" == "1" ]]; then
  SYNC_ARGS+=(--skip-nhsrcl)
fi
run_manage "${SYNC_ARGS[@]}"

echo ""
echo "Done. Sanity check:"
echo "  curl -s http://127.0.0.1:8000/api/health/"
echo "  curl -s http://127.0.0.1:8000/api/news/ | head -c 400"
echo "  curl -s http://127.0.0.1:8000/api/stations/ | head -c 200"