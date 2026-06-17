#!/bin/bash

set -euo pipefail

NTP_SERVERS="${NTP_SERVERS:-192.168.123.161 time.google.com ntp.ubuntu.com}"

DIRECTIVES=()
for s in $NTP_SERVERS; do
    DIRECTIVES+=("server ${s} iburst")
done

echo "ntp-sync-once: syncing clock from: ${NTP_SERVERS}"
if chronyd -q -t 60 "${DIRECTIVES[@]}"; then
    echo "ntp-sync-once: sync complete"
else
    echo "ntp-sync-once: sync timed out or failed, continuing with current clock"
fi
