#!/bin/bash
# Start the Zenoh router in the foreground
# Run this in its own terminal after sourcing setup.sh

LOG_STORE="/tmp/zenohd.log"

if pgrep -x rmw_zenohd > /dev/null 2>&1; then
  echo "[a2_ros] Zenoh router already running (PID: $(pgrep -x rmw_zenohd))"
  exit 0
fi

echo "[a2_ros] Starting Zenoh router (logs also at: $LOG_STORE)"
ros2 run rmw_zenoh_cpp rmw_zenohd 2>&1 | tee "$LOG_STORE"
