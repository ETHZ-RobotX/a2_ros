#!/bin/bash
# Entrypoint for the a2_pc2_joy container.
# This container is started and stopped by autospawn.sh on the host,
# which handles bluetooth detection. By the time this runs, the controller
# is already connected and enumerated. Just run the node.
# restart: unless-stopped restarts the container if joy_node crashes;
# pc2_joylaunch.sh uses `docker compose stop` (which suppresses restart) on disconnect.
set -e
# colcon build --packages-up-to a2_pc2
source /a2_ros/scripts/setup.sh
exec ros2 run joy joy_node --ros-args -p deadzone:=0.05 -p autorepeat_rate:=50.0
