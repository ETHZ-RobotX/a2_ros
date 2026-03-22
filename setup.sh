#!/bin/bash
# A2 Simulation Environment Setup
# Source this file, don't execute it: source setup.sh

SCRIPT_DIR=$(dirname "$(realpath "${BASH_SOURCE[0]}")")

# --- ROS2 ---
source /opt/ros/jazzy/setup.bash

# --- Workspace install ---
if [ -f "$SCRIPT_DIR/install/setup.bash" ]; then
    source "$SCRIPT_DIR/install/setup.bash"
    echo "[a2_ros] Sourced workspace: $SCRIPT_DIR"
else
    echo "[a2_ros] WARNING: Workspace not built yet."
    echo "  Run:  cd $SCRIPT_DIR && colcon build --symlink-install"
fi

# --- Python venv (torch, numpy + inherits ROS2 packages) ---
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    echo "[a2_ros] Activated venv: $SCRIPT_DIR/.venv"
else
    echo "[a2_ros] WARNING: Python venv not found. Run install.sh first."
fi

# --- MuJoCo ---
MUJOCO_DIR="$HOME/.mujoco/mujoco-3.5.0"
export LD_LIBRARY_PATH="$MUJOCO_DIR/lib:${LD_LIBRARY_PATH}"

# --- ROS2 middleware ---
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=1

echo "[a2_ros] ROS_DOMAIN_ID=$ROS_DOMAIN_ID  RMW=$RMW_IMPLEMENTATION"
echo "[a2_ros] Ready."
