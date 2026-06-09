#!/bin/bash

set -euo pipefail

if [ "$EUID" = "0" ]; then
    echo "Please run this script as a normal user (sudo is used where needed)."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_SRC="${SCRIPT_DIR}/ntp-sync-once.service"
SERVICE_DST="/etc/systemd/system/ntp-sync-once.service"
SCRIPT_SRC="${SCRIPT_DIR}/ntp-sync-once.sh"
TARGET_BIN="/usr/local/sbin/ntp-sync-once"
DEFAULTS_DST="/etc/default/ntp-sync-once"

echo "Installing ntp-sync-once systemd unit..."
sudo install -m 0644 "${SERVICE_SRC}" "${SERVICE_DST}"

echo "Installing executable to ${TARGET_BIN}..."
sudo install -m 0755 "${SCRIPT_SRC}" "${TARGET_BIN}"

if [ ! -f "${DEFAULTS_DST}" ]; then
    echo "Creating default config at ${DEFAULTS_DST}..."
    sudo bash -c 'cat > /etc/default/ntp-sync-once <<EOF
# Space-separated list of NTP servers for the one-shot sync
NTP_SERVERS="192.168.123.161 time.google.com ntp.ubuntu.com"
EOF'
fi

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling service to run at boot (once)..."
sudo systemctl enable ntp-sync-once.service

echo "Triggering an immediate one-time sync now..."
sudo systemctl start ntp-sync-once.service

echo "Status:"
systemctl --no-pager status ntp-sync-once.service | cat

echo "Done."
