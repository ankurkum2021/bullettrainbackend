#!/usr/bin/env bash
# Long-running poller (alternative to systemd timer). Use under systemd/supervisor.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INTERVAL="${BTS_NEWS_INTERVAL:-900}"
cd "$ROOT/backend"
exec "$ROOT/backend/env/bin/python" manage.py watch_developments --interval "$INTERVAL" "$@"