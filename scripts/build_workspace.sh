#!/bin/bash
set -e

# Source common
source ./scripts/common.sh

PACKAGE="${1:-}"

source /opt/ros/jazzy/setup.bash
cd "$WORKSPACE_DIR"

if [[ -n "$PACKAGE" ]]; then
    info "Building up to: $PACKAGE"
    colcon build --packages-up-to "$PACKAGE"
else
    info "Building workspace..."
    colcon build
fi
info "Build complete."
