#!/bin/bash
# Configure ROS2 to use CycloneDDS RMW
# Must be sourced, not executed

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "ERROR: This script must be sourced, not executed!"
  echo "Usage: source $(basename "${BASH_SOURCE[0]}") [sim|robot]"
  exit 1
fi

if [[ $# -gt 1 ]]; then
  echo "Error: Too many arguments"
  echo "Usage: source $(basename "${BASH_SOURCE[0]}") [sim|robot]"
  return 1
fi

# Profile selects which config template to render (sim or robot)
# Prefer explicit arg, then PROFILE env var (set in .env), then sim
PROFILE="${1:-${PROFILE:-sim}}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_CONFIG_DIR="$(dirname "$SCRIPT_DIR")"

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="${DEPLOYMENT_CONFIG_DIR}/config/cyclonedds/cyclonedds.${PROFILE}.xml"
# To tap in directly into unitree's dds network
export ROS_DOMAIN_ID=1

echo "[a2_ros] NOTE: CYCLONEDDS configured to listen and publish in the unitree network"
echo "[a2_ros] There is no separate config available currently"
echo "[a2_ros] RMW: CycloneDDS  URI=$CYCLONEDDS_URI"
