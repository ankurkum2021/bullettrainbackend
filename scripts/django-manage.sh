#!/usr/bin/env bash
# Run Django manage.py using backend/env (see npm run api:setup).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
PY="$BACKEND/env/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "Backend venv not found at backend/env." >&2
  echo "Create it with: npm run api:setup" >&2
  exit 1
fi

cd "$BACKEND"
exec "$PY" manage.py "$@"