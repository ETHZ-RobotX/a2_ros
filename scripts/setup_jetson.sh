#!/bin/bash
# Source common
source ./scripts/common.sh

# --- Venv activation ---
VENV_DIR="$WORKSPACE_DIR/venv"
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    info "Activated venv: $VENV_DIR"
else
    warn "Venv not found at $VENV_DIR"
    echo "  Run:  python3 -m venv $VENV_DIR"
fi

# --- Workspace install ---
if [ -f "$WORKSPACE_DIR/install/setup.bash" ]; then
    source "$WORKSPACE_DIR/install/setup.bash"
    info "Sourced workspace: $WORKSPACE_DIR"
else
    warn "Workspace not built yet."
    echo "  Run:  cd $WORKSPACE_DIR && colcon build --symlink-install"
fi

# --- ROS2 middleware ---
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="${WORKSPACE_DIR}/src/core/a2_deployment_config/config/cyclonedds.xml"

info "Jetson Setup."
info "ROS_DOMAIN_ID=$ROS_DOMAIN_ID  RMW=$RMW_IMPLEMENTATION  CYCLONEDDS_URI=$CYCLONEDDS_URI"
info "Ready."
