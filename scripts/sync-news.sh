#!/usr/bin/env bash
# Cron/systemd entry: fetch NHSRCL releases, rewrite, dedupe.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$ROOT/scripts/django-manage.sh" sync_news "$@"