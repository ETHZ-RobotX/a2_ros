#!/bin/bash
# Sourced by .bashrc on shell startup. Lives on the workspace volume so
# changes take effect immediately without rebuilding the image.

# a2 CLI wrapper — intercepts 'source' so it affects this shell;
# all other subcommands are forwarded to the binary in PATH.
a2() {
    if [[ "${1:-}" == "source" ]]; then
        source /a2_ros/scripts/setup.sh
    else
        /usr/local/bin/a2 "$@"
    fi
}
