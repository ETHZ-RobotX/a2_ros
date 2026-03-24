#!/bin/sh
set -e

echo "=== Source Workspace ==="
bash /a2_ros/setup.sh

echo "=== Execute Command ==="
exec "$@"
