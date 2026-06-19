#!/bin/bash
# PC2 startup script — run once at boot (e.g. via systemd).
#
# zenoh + bridge are always-on: compose restart: unless-stopped keeps them alive
# after this script exits or if they crash. This script only needs to bring them
# up once at boot.
#
# The joy container is managed here: started when the PS5 controller connects
# over bluetooth, stopped when it disconnects. `docker compose stop` sets the
# "manually stopped" flag, so restart: unless-stopped does NOT auto-restart it
# on disconnect — only this script can bring it back up.
set -e

MAC="D4:2F:4B:B3:F5:4A"
COMPOSE_FILE="$(dirname "$(realpath "$0")")/../../compose.pc2.yaml"
DC="docker compose -f $COMPOSE_FILE"

cleanup() {
  echo "$(date): caught signal — stopping joy container and exiting"
  $DC stop a2_pc2_joy 2>/dev/null || true
  exit 0
}
trap cleanup SIGTERM SIGINT

# Bring up always-on services. Compose restart policy keeps them alive from here on.
echo "$(date): starting zenoh router and bridge"
$DC up -d zenoh_router_robot a2_pc2_bridge

bt_connected() {
  bluetoothctl info "$MAC" 2>/dev/null | grep -q "Connected: yes"
}

# The kernel takes a moment after BT connects to enumerate /dev/input/jsN.
# Wait for it before starting the joy container so joy_node opens the device cleanly.
joy_device_ready() {
  ls /dev/input/js* > /dev/null 2>&1
}

echo "$(date): entering bluetooth watch loop (MAC: $MAC)"
while true; do
  until bt_connected; do sleep 1; done
  echo "$(date): controller connected — waiting for input device enumeration"

  attempts=0
  until joy_device_ready; do
    if ! bt_connected; then
      echo "$(date): disconnected before device was ready — looping back"
      break
    fi
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 20 ]; then
      echo "$(date): input device not enumerated after 10s — looping back"
      break
    fi
    sleep 0.5
  done

  if ! joy_device_ready; then
    continue
  fi

  echo "$(date): starting joy container"
  $DC up -d a2_pc2_joy

  while bt_connected; do sleep 1; done

  echo "$(date): controller disconnected — stopping joy container"
  $DC stop a2_pc2_joy
done
