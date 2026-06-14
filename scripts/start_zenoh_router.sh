#!/bin/bash
# Start the Zenoh router in the foreground
# Run this in its own terminal after sourcing setup.sh

LOG_STORE="/tmp/zenohd.log"

# A router may already be running in this container (pgrep) or in a separate
# container on the shared host network (TCP port probe — pgrep can't see it).
if pgrep -x rmw_zenohd > /dev/null 2>&1; then
  echo "[a2_ros] Zenoh router already running here (PID: $(pgrep -x rmw_zenohd))"
  exit 0
fi
if timeout 1 bash -c "exec 3<>/dev/tcp/127.0.0.1/7447" 2>/dev/null; then
  echo "[a2_ros] A Zenoh router is already listening on 127.0.0.1:7447 (likely the compose service)."
  exit 0
fi

echo "[a2_ros] Starting Zenoh router (logs also at: $LOG_STORE)"
ros2 run rmw_zenoh_cpp rmw_zenohd 2>&1 | tee "$LOG_STORE"
