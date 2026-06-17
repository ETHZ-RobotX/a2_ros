#!/bin/bash

set -euo pipefail

if [ "$EUID" = "0" ]; then
    echo "Please run this script as a normal user (sudo is used where needed)."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PTP4L_SRC="${SCRIPT_DIR}/ptp4l-master.service"
PTP4L_DST="/etc/systemd/system/ptp4l-master.service"

echo "Installing ptp4l-master.service..."
sudo install -m 0644 "${PTP4L_SRC}" "${PTP4L_DST}"

echo "Disabling phc2sys (PHC broken on this kernel)..."
sudo systemctl disable --now phc2sys-net1.service 2>/dev/null || true

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling ptp4l..."
sudo systemctl enable ptp4l-master.service

echo "Starting ptp4l..."
sudo systemctl restart ptp4l-master.service

echo "Status:"
systemctl --no-pager status ptp4l-master.service | cat

echo "Done."
