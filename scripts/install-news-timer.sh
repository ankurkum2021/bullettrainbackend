#!/usr/bin/env bash
#
# Install systemd timer for automated NHSRCL news sync (Lightsail / VPS).
#
# Usage:
#   sudo BTS_INSTALL_ROOT=/opt/bullettrainstation bash scripts/install-news-timer.sh
#
set -euo pipefail

ROOT="${BTS_INSTALL_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
UNIT_DIR="/etc/systemd/system"
SERVICE_SRC="$ROOT/deploy/systemd/bts-news-sync.service"
TIMER_SRC="$ROOT/deploy/systemd/bts-news-sync.timer"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-run with sudo." >&2
  exit 1
fi

if [[ ! -x "$ROOT/backend/env/bin/python" ]]; then
  echo "Missing venv at $ROOT/backend/env — run lightsail-backend-bootstrap.sh first." >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

sed -e "s|/opt/bullettrainstation|$ROOT|g" "$SERVICE_SRC" >"$tmpdir/bts-news-sync.service"
cp "$TIMER_SRC" "$tmpdir/bts-news-sync.timer"

install -m 0644 "$tmpdir/bts-news-sync.service" "$UNIT_DIR/bts-news-sync.service"
install -m 0644 "$tmpdir/bts-news-sync.timer" "$UNIT_DIR/bts-news-sync.timer"

systemctl daemon-reload
systemctl enable --now bts-news-sync.timer
systemctl start bts-news-sync.service || true

echo "Installed bts-news-sync.timer (every 15 min)."
echo "  systemctl status bts-news-sync.timer"
echo "  journalctl -u bts-news-sync.service -n 30 --no-pager"