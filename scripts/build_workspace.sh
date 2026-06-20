#!/bin/bash
set -e

# Source common
source ./scripts/common.sh

PACKAGE="${1:-}"
shift || true
EXTRA_ARGS=("$@")

source /opt/ros/jazzy/setup.bash
cd "$WORKSPACE_DIR"

# Cap build parallelism to half the available cores so a build doesn't starve
# the machine (the committed colcon defaults can't compute this — they're read
# verbatim). The CLI flag overrides parallel-workers from $COLCON_DEFAULTS_FILE.
# Override the worker count with A2_BUILD_JOBS.
CORES="$(nproc 2>/dev/null || echo 2)"
JOBS="${A2_BUILD_JOBS:-$(( CORES / 2 ))}"
[[ "$JOBS" -lt 1 ]] && JOBS=1

# --executor overrides the parallel-workers default (sequential ignores it);
# skip the flag when the caller already supplied --executor.
WORKER_ARGS=(--parallel-workers "$JOBS")
for arg in "${EXTRA_ARGS[@]}"; do
    [[ "$arg" == "--executor" || "$arg" == --executor=* ]] && WORKER_ARGS=() && break
done
[[ ${#WORKER_ARGS[@]} -gt 0 ]] && info "Parallel workers: ${JOBS} (of ${CORES} cores)"

if [[ -n "$PACKAGE" ]]; then
    info "Building up to: $PACKAGE"
    colcon build --packages-up-to "$PACKAGE" "${WORKER_ARGS[@]}" "${EXTRA_ARGS[@]}"
else
    info "Building workspace..."
    colcon build "${WORKER_ARGS[@]}" "${EXTRA_ARGS[@]}"
fi
info "Build complete."
