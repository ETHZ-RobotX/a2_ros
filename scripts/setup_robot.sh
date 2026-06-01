#!/bin/bash

# Source common
source ./scripts/common.sh

# --- Workspace install ---
if [ -f "$WORKSPACE_DIR/install/setup.bash" ]; then
    source "$WORKSPACE_DIR/install/setup.bash"
    echo "[a2_ros] Sourced workspace: $WORKSPACE_DIR"
else
    echo "[a2_ros] WARNING: Workspace not built yet."
    echo "  Run:  cd $WORKSPACE_DIR && colcon build --symlink-install"
fi

# --- ROS2 middleware ---
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="${WORKSPACE_DIR}/src/core/a2_deployment_config/config/cyclonedds.xml"

echo "[a2_ros] Robot Setup."
echo "[a2_ros] ROS_DOMAIN_ID=$ROS_DOMAIN_ID  RMW=$RMW_IMPLEMENTATION CYCLONEDDS_URI=$CYCLONEDDS_URI"
echo "[a2_ros] Ready."
