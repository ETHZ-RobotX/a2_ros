#!/bin/bash
# A2 Simulation Environment Setup
# Source this file, don't execute it: source setup.sh

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

# --- Python venv (torch, numpy + inherits ROS 2 packages) ---
if [ -f "$WORKSPACE_DIR/.venv/bin/activate" ]; then
    source "$WORKSPACE_DIR/.venv/bin/activate"
    echo "[a2_ros] Activated venv: $WORKSPACE_DIR/.venv"
else
    error " [a2_ros] WARNING: Python venv not found."
fi

# --- MuJoCo ---
export MUJOCO_DIR="${MUJOCO_DIR:-/opt/mujoco/mujoco-3.5.0}"
export LD_LIBRARY_PATH="$MUJOCO_DIR/lib:${LD_LIBRARY_PATH}"

# --- MuJoCo symlink required by unitree_mujoco ---
MUJOCO_SYMLINK="$WORKSPACE_DIR/external/unitree_mujoco/simulate/mujoco"
if [ ! -L "$MUJOCO_SYMLINK" ]; then
    ln -sf "$MUJOCO_DIR" "$MUJOCO_SYMLINK"
    echo "[a2_ros] Created MuJoCo symlink: $MUJOCO_SYMLINK -> $MUJOCO_DIR"
fi

export USER=root
# --- ROS2 middleware ---
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=1
export CYCLONEDDS_URI='<CycloneDDS><Domain><General><Interfaces><NetworkInterface name="lo" priority="default" multicast="default" /></Interfaces></General></Domain></CycloneDDS>'

echo "[a2_ros] ROS_DOMAIN_ID=$ROS_DOMAIN_ID  RMW=$RMW_IMPLEMENTATION"
echo "[a2_ros] Ready."
