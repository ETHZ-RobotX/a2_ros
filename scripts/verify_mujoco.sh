#!/bin/bash
set -e

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

MUJOCO_DIR="${MUJOCO_DIR:-$HOME/.mujoco/mujoco-3.5.0}"
MUJOCO_VERSION=$(basename "$MUJOCO_DIR" | cut -d- -f2-)

info "Verifying MuJoCo ${MUJOCO_VERSION} at ${MUJOCO_DIR}..."

SIMULATE="$MUJOCO_DIR/bin/simulate"
SAMPLE_MODEL=$(find "$MUJOCO_DIR/model" -name "*.xml" | head -1)

if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    info "Display detected. Opening MuJoCo viewer (close the window to finish)..."
    "$SIMULATE" "$SAMPLE_MODEL"
    info "MuJoCo opened successfully — installation verified."
else
    info "Headless environment. Checking MuJoCo library..."
    python3 - <<EOF
import ctypes, sys
try:
    ctypes.cdll.LoadLibrary("$MUJOCO_DIR/lib/libmujoco.so.$MUJOCO_VERSION")
    print("  MuJoCo library loads correctly.")
except OSError as e:
    print(f"  ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF
fi
