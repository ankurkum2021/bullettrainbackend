#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
cd "$BACKEND"

if [[ ! -d env ]]; then
  python3 -m venv env
fi

./env/bin/pip install -q -r requirements.txt
./env/bin/python manage.py migrate

echo "Backend ready. Start API: npm run api:dev"