#!/bin/bash
set -e

# Source common
source ./scripts/common.sh

PACKAGE="${1:-}"

source /opt/ros/jazzy/setup.bash
cd "$WORKSPACE_DIR"

if [[ -n "$PACKAGE" ]]; then
    info "Building up to: $PACKAGE"
    colcon build --symlink-install --packages-up-to "$PACKAGE"
else
    info "Building workspace..."
    # unitree_mujoco uses /proc/self/exe to locate its install prefix, so its binary
    # must be physically copied (not symlinked) — build it separately without --symlink-install.
    colcon build --symlink-install --packages-skip unitree_mujoco
    if [ "${A2_MODE}" = "sim" ]; then
        colcon build --packages-select unitree_mujoco
    fi
fi
info "Build complete."
