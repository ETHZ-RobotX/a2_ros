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

# Router IP resolution order:
#   1. explicit 2nd arg
#   2. per-profile override: ZENOH_ROUTER_IP_SIM / ZENOH_ROUTER_IP_ROBOT
#   3. generic ZENOH_ROUTER_IP (shared fallback)
#   4. localhost
_PROFILE_IP_VAR="ZENOH_ROUTER_IP_$(echo "$ZENOH_PROFILE" | tr '[:lower:]' '[:upper:]')"
ROUTER_IP="${2:-${!_PROFILE_IP_VAR:-${ZENOH_ROUTER_IP:-127.0.0.1}}}"

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

# The Unitree SDK bridge (a2_unitree_bridge) talks to the MuJoCo sim over Unitree's
# own CycloneDDS regardless of the ROS RMW. Point its CycloneDDS at the tuned sim
# profile so large samples (e.g. the front lidar PointCloud2) fragment and buffer
# correctly. rmw_zenoh ignores CYCLONEDDS_URI, so this is safe under Zenoh.
#
# Sim only: in robot mode we leave CYCLONEDDS_URI unset so the bridge keeps the
# Unitree SDK's own (hardware-validated) CycloneDDS defaults. Pointing it at
# cyclonedds.robot.xml here would silently change tested robot DDS behavior on PC2.
if [[ "$ZENOH_PROFILE" == "sim" ]]; then
  DEPLOYMENT_CONFIG_DIR="$(dirname "$SCRIPT_DIR")"
  export CYCLONEDDS_URI="${DEPLOYMENT_CONFIG_DIR}/config/cyclonedds/cyclonedds.sim.xml"
fi

# Isolate the Zenoh (sim) network on its own ROS domain. Override in .env if needed.
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-30}"

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

# Use `command mv` to bypass the interactive shell's `mv -iv` alias (which
# would otherwise print a "renamed ..." line on every shell startup).
command mv -f "$TEMP_CONFIG" "$FINAL_CONFIG"
export ZENOH_SESSION_CONFIG_URI="$FINAL_CONFIG"

echo "[a2_ros] Zenoh session config: $FINAL_CONFIG"
echo "[a2_ros] ROS_DOMAIN_ID=$ROS_DOMAIN_ID"

# Warn if the router isn't reachable — nodes will connect once it starts.
# We probe the TCP port rather than using pgrep: the router runs in a separate
# container (shared host network), so its process isn't visible in this
# container's PID namespace. A port probe also works for a remote router.
if ! timeout 1 bash -c "exec 3<>/dev/tcp/${ROUTER_IP}/7447" 2>/dev/null; then
  echo "[a2_ros] WARNING: Zenoh router not reachable at ${ROUTER_IP}:7447."
  echo "[a2_ros]   It should autostart via compose (service: zenoh_router_${ZENOH_PROFILE})."
  echo "[a2_ros]   Manual fallback: scripts/start_zenoh_router.sh"
fi
