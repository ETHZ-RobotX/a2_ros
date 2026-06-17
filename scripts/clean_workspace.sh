#!/bin/bash
set -e

# Source common
source ./scripts/common.sh

# ---------------------------------------------------------------
# Clean workspace — removes colcon build artefacts.
# ---------------------------------------------------------------
TARGETS=("build" "install" "log")

warn "This will delete the following directories under $WORKSPACE_DIR:"
for dir in "${TARGETS[@]}"; do
    if [ -d "$WORKSPACE_DIR/$dir" ]; then
        echo "    $WORKSPACE_DIR/$dir"
    fi
done

read -r -p "$(echo -e "${YELLOW}[WARN]${NC}  Continue? [y/N] ")" confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    info "Aborted."
    exit 0
fi

info "Cleaning workspace..."
for dir in "${TARGETS[@]}"; do
    target="$WORKSPACE_DIR/$dir"
    if [ -d "$target" ]; then
        # Remove contents only — the directory itself may be a Docker volume mount point
        rm -rf "${target:?}/"*
        info "  Cleaned: $target"
    else
        info "  Skipped (not found): $target"
    fi
done

info "Clean complete. Run build_workspace.sh to rebuild."