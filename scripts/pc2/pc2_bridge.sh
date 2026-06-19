#!/bin/bash
# Entrypoint for the a2_pc2_bridge container.
# Builds the PC2 packages, sources the workspace, and runs the launch file.
# Build runs first so the install is fresh before setup.sh sources it.
# restart: unless-stopped in compose keeps this alive on crashes.
set -e
colcon build --packages-up-to a2_pc2
source /a2_ros/scripts/setup.sh
exec ros2 launch a2_pc2 pc2.launch.py
