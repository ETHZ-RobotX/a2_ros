#!/bin/bash
set -e

# Source common
source ./scripts/common.sh

# ---------------------------------------------------------------
# Clean workspace — removes colcon build artefacts.
# Artefacts live in $A2_WS_ROOT (set in the Docker image, outside the source
# tree); fall back to the source dir for native builds.
# ---------------------------------------------------------------
WS_ART="${A2_WS_ROOT:-$WORKSPACE_DIR}"
TARGETS=("$WS_ART/build" "$WS_ART/install" "$WS_ART/log")

warn "This will delete the following directories:"
for target in "${TARGETS[@]}"; do
    if [ -d "$target" ]; then
        echo "    $target"
    fi
done

read -r -p "$(echo -e "${YELLOW}[WARN]${NC}  Continue? [y/N] ")" confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    info "Aborted."
    exit 0
fi

info "Cleaning workspace..."
for target in "${TARGETS[@]}"; do
    if [ -d "$target" ]; then
        # Remove contents only — the directory itself may be a Docker volume mount
        # point. -mindepth 1 keeps the dir; -delete also clears hidden files such
        # as .colcon_install_layout, which a plain `rm -rf dir/*` would miss and
        # which would otherwise cause colcon install-layout clashes.
        find "${target:?}" -mindepth 1 -delete
        info "  Cleaned: $target"
    else
        info "  Skipped (not found): $target"
    fi
done

info "Clean complete. Run build_workspace.sh to rebuild."