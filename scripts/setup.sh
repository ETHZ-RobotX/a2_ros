#!/bin/bash
# A2 Environment Setup
# Source this file, don't execute it: source setup.sh
# Mode (sim|robot) is controlled by the A2_MODE env var set in the Docker image.

_SETUP_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$_SETUP_SCRIPT_DIR/common.sh"

# --- Workspace install ---
if [ -f "$WORKSPACE_DIR/install/setup.bash" ]; then
    source "$WORKSPACE_DIR/install/setup.bash"
    echo "[a2_ros] Sourced workspace: $WORKSPACE_DIR"
else
    echo "[a2_ros] WARNING: Workspace not built yet."
    echo "  Run:  cd $WORKSPACE_DIR && colcon build --symlink-install"
fi

# --- MuJoCo (sim only) ---
if [ "$A2_MODE" = "sim" ]; then
    export MUJOCO_DIR="${MUJOCO_DIR:-/opt/mujoco/mujoco-3.5.0}"
    export LD_LIBRARY_PATH="$MUJOCO_DIR/lib:${LD_LIBRARY_PATH}"

    MUJOCO_SYMLINK="$WORKSPACE_DIR/external/unitree_mujoco/simulate/mujoco"
    if [ ! -L "$MUJOCO_SYMLINK" ]; then
        ln -sf "$MUJOCO_DIR" "$MUJOCO_SYMLINK"
        echo "[a2_ros] Created MuJoCo symlink: $MUJOCO_SYMLINK -> $MUJOCO_DIR"
    fi
fi

# --- ROS2 middleware (controlled by RMW_IMPLEMENTATION in .env) ---
DEPLOYMENT_SCRIPTS="$WORKSPACE_DIR/src/core/a2_deployment_config/scripts"
_RMW="${RMW_IMPLEMENTATION:-rmw_zenoh_cpp}"
echo "[a2_ros] RMW: $_RMW"
case "$_RMW" in
    rmw_zenoh_cpp)
        source "$DEPLOYMENT_SCRIPTS/setup_zenoh.sh" "$A2_MODE"
        ;;
    rmw_cyclonedds_cpp)
        source "$DEPLOYMENT_SCRIPTS/setup_cyclonedds.sh" "$A2_MODE"
        ;;
    *)
        warn "Unknown RMW_IMPLEMENTATION=${_RMW} — skipping middleware setup"
        ;;
esac

echo "[a2_ros] Ready. (mode: $A2_MODE)"
