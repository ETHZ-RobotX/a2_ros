#!/bin/bash
# Run once from the repo root to populate .env with your host UID/GID.
# After this, `docker compose run --rm a2_ros_dev` picks up the right values
# automatically without any per-command prefix.
set -e

ENV_FILE="$(dirname "$0")/../.env"

grep -q "^HOST_UID=" "$ENV_FILE" 2>/dev/null || echo "HOST_UID=$(id -u)" >> "$ENV_FILE"
grep -q "^HOST_GID=" "$ENV_FILE" 2>/dev/null || echo "HOST_GID=$(id -g)" >> "$ENV_FILE"
# /dev/input group GID — lets the container read the joystick. `getent` and an
# `input` group only exist on Linux; on macOS (no getent, no /dev/input) fall
# back to 107 — harmless, since there's no joystick passthrough there anyway.
INPUT_GID="$(getent group input 2>/dev/null | cut -d: -f3)"
INPUT_GID="${INPUT_GID:-107}"
grep -q "^INPUT_GID=" "$ENV_FILE" 2>/dev/null || echo "INPUT_GID=${INPUT_GID}" >> "$ENV_FILE"

# Robot PC's static IP on the lab network — needed so the NUC's Zenoh client
# can find the robot's router (see ZENOH_ROUTER_IP_ROBOT in README.md).
grep -q "^ZENOH_ROUTER_IP_ROBOT=" "$ENV_FILE" 2>/dev/null || echo "ZENOH_ROUTER_IP_ROBOT=192.168.124.162" >> "$ENV_FILE"

echo "Host UID=$(id -u) GID=$(id -g) INPUT_GID=${INPUT_GID} written to .env"
