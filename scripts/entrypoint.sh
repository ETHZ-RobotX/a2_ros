#!/bin/sh
set -e

echo "=== Source Workspace ==="
bash /a2_ros/scripts/setup.sh

echo "=== Fix SSH Permissions ==="
if [ -d /root/.ssh ]; then
  chown -R root:root /root/.ssh
  chmod 700 /root/.ssh
  chmod 600 /root/.ssh/* 2>/dev/null || true
fi

echo "=== Execute Command ==="
exec "$@"
