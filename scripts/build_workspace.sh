#!/bin/bash
set -e

# Source common
source ./scripts/common.sh

PACKAGE="${1:-}"

source /opt/ros/jazzy/setup.bash
cd "$WORKSPACE_DIR"

# Cap build parallelism to half the available cores so a build doesn't starve
# the machine (the committed colcon defaults can't compute this — they're read
# verbatim). The CLI flag overrides parallel-workers from $COLCON_DEFAULTS_FILE.
# Override the worker count with A2_BUILD_JOBS.
CORES="$(nproc 2>/dev/null || echo 2)"
JOBS="${A2_BUILD_JOBS:-$(( CORES / 2 ))}"
[[ "$JOBS" -lt 1 ]] && JOBS=1
info "Parallel workers: ${JOBS} (of ${CORES} cores)"

if [[ -n "$PACKAGE" ]]; then
    info "Building up to: $PACKAGE"
    colcon build --packages-up-to "$PACKAGE" --parallel-workers "$JOBS"
else
    info "Building workspace..."
    colcon build --parallel-workers "$JOBS"
fi
info "Build complete."
