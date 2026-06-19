#!/bin/bash
# A2 Environment Setup
# Source this file, don't execute it: source setup.sh
# Mode (sim|robot) is controlled by the A2_MODE env var set in the Docker image.

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: Do not execute this script directly. Source it instead:"
    echo "  source ./scripts/setup.sh"
    exit 1
fi

_SETUP_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$_SETUP_SCRIPT_DIR/common.sh"

# --- Workspace install ---
# Colcon artefacts live in $A2_WS_ROOT (set in the Docker image, outside the
# bind-mounted source tree); fall back to the source dir for native builds.
_WS_ROOT="${A2_WS_ROOT:-$WORKSPACE_DIR}"
if [ -f "$_WS_ROOT/install/setup.bash" ]; then
    source "$_WS_ROOT/install/setup.bash"
    echo "[a2_ros] Sourced workspace: $_WS_ROOT"
else
    echo "[a2_ros] WARNING: Workspace not built yet."
    echo "  Run:  ./scripts/build_workspace.sh"
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
