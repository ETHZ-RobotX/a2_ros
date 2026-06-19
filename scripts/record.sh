#!/bin/bash
set -e

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

# ---------------------------------------------------------------
# Record ROS 2 topics to MCAP format.
# Bags are written to $ROS_BAGS_DIR (default: $A2_WS_ROOT/bags, i.e. the
# workspace artefacts root, falling back to $WORKSPACE_DIR/bags outside the
# container).
#
# YAML config format (--config):
#   all: true
#   topics:
#     - /cmd_vel
#     - /odom
#   ignore:
#     - /camera/image_raw
# ---------------------------------------------------------------

_usage() {
    cat <<EOF
Usage: record.sh [OPTIONS] [SUFFIX]

Options:
  -a, --all            Record all topics
  -t, --topics <list>  Space-separated topics to record (quoted)
  -i, --ignore <list>  Space-separated topics to exclude (quoted)
  -c, --config <file>  YAML config file (overrides -a/-t/-i if set)
  -h, --help           Show this help

Examples:
  record.sh --all
  record.sh --all --ignore '/camera/image_raw /diagnostics' run1
  record.sh --topics '/cmd_vel /odom /imu/data' flight_test
  record.sh --config config/record_nav.yaml
EOF
}

TOPICS=""
IGNORE_TOPICS=""
RECORD_ALL=false
CONFIG=""
SUFFIX=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -a|--all)    RECORD_ALL=true; shift ;;
        -t|--topics) TOPICS="$2"; shift 2 ;;
        -i|--ignore) IGNORE_TOPICS="$2"; shift 2 ;;
        -c|--config) CONFIG="$2"; shift 2 ;;
        -h|--help)   _usage; exit 0 ;;
        -*)          error "Unknown option: $1"; _usage; exit 1 ;;
        *)           SUFFIX="$1"; shift ;;
    esac
done

# --- YAML config (overrides CLI flags) ---
if [[ -n "$CONFIG" ]]; then
    if [[ ! -f "$CONFIG" ]]; then
        error "Config file not found: $CONFIG"
        exit 1
    fi
    eval "$(python3 - "$CONFIG" <<'PYEOF'
import yaml, sys, shlex
with open(sys.argv[1]) as f:
    c = yaml.safe_load(f)
if c.get("all"):
    print("RECORD_ALL=true")
if c.get("topics"):
    print("TOPICS=" + shlex.quote(" ".join(c["topics"])))
if c.get("ignore"):
    print("IGNORE_TOPICS=" + shlex.quote(" ".join(c["ignore"])))
PYEOF
)"
fi

# --- Validate ---
if ! $RECORD_ALL && [[ -z "$TOPICS" ]]; then
    error "No topics specified. Use --all or --topics, or provide a --config file."
    echo
    _usage
    exit 1
fi

# --- Output path ---
BAG_DIR="${ROS_BAGS_DIR:-${A2_WS_ROOT:-$WORKSPACE_DIR}/bags}"
mkdir -p "$BAG_DIR"
STAMP=$(date +"%Y%m%d_%H%M%S")
OUT="$BAG_DIR/bag_${STAMP}${SUFFIX:+_$SUFFIX}"

# --- Build command ---
CMD=(ros2 bag record --storage mcap -o "$OUT")
if $RECORD_ALL; then
    CMD+=(-a)
    [[ -n "$IGNORE_TOPICS" ]] && CMD+=(--exclude-topics $IGNORE_TOPICS)
else
    CMD+=($TOPICS)
fi

info "Recording to: $OUT"
info "Command: ${CMD[*]}"
info "Press Ctrl+C to stop."
echo
"${CMD[@]}"
