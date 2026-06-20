#!/bin/bash

set -euo pipefail

if [ "$EUID" = "0" ]; then
    echo "Please run this script as a normal user (sudo is used where needed)."
    exit 1
fi

if ! command -v sudo > /dev/null 2>&1; then
    echo "Warning: 'sudo' not found. This script needs root privileges to write"
    echo "sysctl settings. Install sudo or run the sysctl steps manually as root."
    exit 1
fi

SYSCTL_DST="/etc/sysctl.d/60-a2-network.conf"

echo "Writing sysctl settings to ${SYSCTL_DST}..."
sudo tee "${SYSCTL_DST}" > /dev/null <<'EOF'
# Network host tuning for a2_ros (large DDS message support)
net.core.rmem_max = 2147483647
net.ipv4.ipfrag_time = 3
net.ipv4.ipfrag_high_thresh = 134217728
EOF

echo "Applying sysctl settings..."
sudo sysctl -p "${SYSCTL_DST}"

echo "Current values:"
sysctl net.core.rmem_max net.ipv4.ipfrag_time net.ipv4.ipfrag_high_thresh

echo "Done."
