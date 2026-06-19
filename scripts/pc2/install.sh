#!/bin/bash
# Install the PC2 systemd service on the PC2 machine.
# Run once after cloning/pulling the repo:
#   bash scripts/pc2/install.sh
set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SERVICE_FILE="$REPO_ROOT/scripts/pc2/pc2_launch.service"

echo "Repo root: $REPO_ROOT"

# Symlink pc2_joylaunch.sh so the service file path stays static across repo moves
echo "Symlinking pc2_joylaunch.sh -> /usr/local/bin/pc2_joylaunch.sh"
sudo ln -sf "$REPO_ROOT/scripts/pc2/pc2_joylaunch.sh" /usr/local/bin/pc2_joylaunch.sh

echo "Installing pc2_launch.service"
sudo cp "$SERVICE_FILE" /etc/systemd/system/pc2_launch.service
sudo systemctl daemon-reload
sudo systemctl enable pc2_launch.service

echo ""
echo "Done. Commands:"
echo "  sudo systemctl start pc2_launch.service   # start now"
echo "  journalctl -u pc2_launch.service -f       # watch logs"
