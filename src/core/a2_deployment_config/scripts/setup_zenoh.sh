#!/bin/bash
# Configure ROS2 to use Zenoh RMW (client environment only)
# Start the router separately: scripts/start_zenoh_router.sh
# Must be sourced, not executed

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "ERROR: This script must be sourced, not executed!"
  echo "Usage: source $(basename "${BASH_SOURCE[0]}") [sim|robot] [router_ip]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Profile selects which config template to render (sim or robot)
# Prefer explicit arg, then ZENOH_PROFILE env var (set in .env), then sim
ZENOH_PROFILE="${1:-${ZENOH_PROFILE:-sim}}"

# Router IP: prefer explicit arg, then ZENOH_ROUTER_IP env var, then localhost
ROUTER_IP="${2:-${ZENOH_ROUTER_IP:-127.0.0.1}}"

if [[ $# -gt 2 ]]; then
  echo "Error: Too many arguments"
  echo "Usage: source $(basename "${BASH_SOURCE[0]}") [sim|robot] [router_ip]"
  return 1
fi

if [[ "$ROUTER_IP" == "127.0.0.1" ]]; then
  echo "[a2_ros] Zenoh: localhost"
else
  echo "[a2_ros] Zenoh: connecting to router at $ROUTER_IP"
fi

export RMW_IMPLEMENTATION=rmw_zenoh_cpp

# Render session config from template
CONFIG_DIR="${HOME}/.tmp"
mkdir -p "$CONFIG_DIR"
FINAL_CONFIG="${CONFIG_DIR}/zenoh-ros2-config.${ZENOH_PROFILE}.json5"
TEMP_CONFIG="${FINAL_CONFIG}.new"

python3 "$SCRIPT_DIR/render_zenoh_config.py" \
  --profile "$ZENOH_PROFILE" \
  --router-ip "$ROUTER_IP" \
  --output-file "$TEMP_CONFIG"

# Restart ROS2 daemon only if config changed
if [[ -f "$FINAL_CONFIG" ]]; then
  if ! cmp -s "$TEMP_CONFIG" "$FINAL_CONFIG"; then
    echo "[a2_ros] Zenoh config changed — restarting ROS2 daemon..."
    ros2 daemon stop > /dev/null 2>&1 || true
  fi
fi

mv -f "$TEMP_CONFIG" "$FINAL_CONFIG"
export ZENOH_SESSION_CONFIG_URI="$FINAL_CONFIG"

echo "[a2_ros] Zenoh session config: $FINAL_CONFIG"

# Warn if router is not running — nodes will connect once it starts
if ! pgrep -x rmw_zenohd > /dev/null 2>&1; then
  echo "[a2_ros] WARNING: Zenoh router is not running."
  echo "[a2_ros]   Start it in a separate terminal: scripts/start_zenoh_router.sh"
fi
