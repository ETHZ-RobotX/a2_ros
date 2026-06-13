#!/bin/bash
# Run once from the repo root to populate .env with your host UID/GID.
# After this, `docker compose run --rm a2_ros_dev` picks up the right values
# automatically without any per-command prefix.
set -e

ENV_FILE="$(dirname "$0")/../.env"

grep -q "^HOST_UID=" "$ENV_FILE" 2>/dev/null || echo "HOST_UID=$(id -u)" >> "$ENV_FILE"
grep -q "^HOST_GID=" "$ENV_FILE" 2>/dev/null || echo "HOST_GID=$(id -g)" >> "$ENV_FILE"

echo "Host UID=$(id -u) GID=$(id -g) written to .env"
