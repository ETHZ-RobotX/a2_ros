#!/bin/bash
set -e

source "./scripts/common.sh"

info "Initialising git submodules..."

# unitree_mujoco expects a real directory at this path; remove the symlink so
# git can check out the submodule into it.
MUJOCO_SYMLINK="$WORKSPACE_DIR/external/unitree_mujoco/simulate/mujoco"
[ -L "$MUJOCO_SYMLINK" ] && rm "$MUJOCO_SYMLINK"

git -C "$WORKSPACE_DIR" submodule update --init --recursive
info "Submodules ready."
