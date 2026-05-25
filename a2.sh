#!/bin/bash
set -e

REPO_DIR=$(dirname "$(realpath "${BASH_SOURCE[0]}")")

# Deactivate conda (nested envs too) — conda Python breaks ROS2 builds and launches
if [ -n "$CONDA_PREFIX" ]; then
    eval "$(conda shell.bash hook 2>/dev/null)"
    while [ -n "$CONDA_PREFIX" ]; do
        conda deactivate
    done
fi

source "$REPO_DIR/scripts/local/setup.sh"

RVIZ=false
CMD=""
for arg in "$@"; do
  case "$arg" in
    --rviz) RVIZ=true ;;
    --*)    CMD="$arg" ;;
  esac
done

case "$CMD" in
  --start)
    ros2 launch a2_ros sim.launch.py scene:=scene_maze.xml rviz:=$RVIZ
    ;;
  --source)
    source "$REPO_DIR/scripts/local/setup.sh"
    ;;
  --bashrc)
    if grep -q "# a2_ros" "$HOME/.bashrc" 2>/dev/null; then
        echo "a2 function already in ~/.bashrc — nothing to do."
    else
        cat >> "$HOME/.bashrc" <<EOF

# a2_ros
a2() {
    if [ "\$1" = "--source" ]; then
        source "$REPO_DIR/scripts/local/setup.sh"
    else
        "$REPO_DIR/a2.sh" "\$@"
    fi
}
EOF
        echo "Added 'a2' function to ~/.bashrc."
    fi
    # Only works if this script is being sourced (not executed as a subprocess)
    if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
        source "$HOME/.bashrc"
        echo "a2 is now active in this terminal."
    else
        echo "Run 'source ./a2.sh --bashrc' for it to take effect immediately."
    fi
    ;;
  --walk)
    # 1=sit  2=stand  3=walk
    ros2 topic pub --once /mode std_msgs/msg/Int32 "data: 3"
    ;;
  --nav)
    ros2 launch a2_ros navigation.launch.py rviz:=$RVIZ
    ;;
  --exploration)
    ros2 launch a2_ros exploration.launch.py rviz:=$RVIZ
    ;;
  --dlio)
    ros2 launch a2_ros dlio.launch.py rviz:=$RVIZ
    ;;
  *)
    echo "Usage: $0 {--start|--walk|--nav|--exploration|--dlio|--source|--bashrc} [--rviz]"
    echo ""
    echo "  --start        Launch the MuJoCo simulation"
    echo "  --walk         Command the robot to walk (publishes mode=3)"
    echo "  --nav          Launch the navigation stack"
    echo "  --exploration  Launch autonomous exploration (TARE)"
    echo "  --dlio         Launch DLIO LiDAR-inertial odometry"
    echo "  --source       Source the workspace setup"
    echo "  --bashrc       Add the 'a2' shell function to ~/.bashrc"
    echo "  --rviz         Open RViz alongside the launch"
    exit 1
    ;;
esac
