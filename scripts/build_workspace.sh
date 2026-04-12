#!/bin/bash
set -e

# Source common
source ./scripts/common.sh

# ---------------------------------------------------------------
# Build workspace (builds inside the repo directory)
# Venv must NOT be active here — colcon needs system Python.
# ---------------------------------------------------------------
info "Building workspace..."
source /opt/ros/jazzy/setup.bash
cd "$WORKSPACE_DIR"
# unitree_mujoco uses /proc/self/exe to locate its install prefix, so its binary
# must be physically copied (not symlinked) — build it separately without --symlink-install.
colcon build --symlink-install --packages-skip unitree_mujoco
colcon build --packages-select unitree_mujoco
info "Build complete."
