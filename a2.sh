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
DLIO=false
CMD=""
for arg in "$@"; do
  case "$arg" in
    --rviz) RVIZ=true ;;
    --dlio) DLIO=true ;;
    --*)    CMD="$arg" ;;
  esac
done

case "$CMD" in
  --start)
    ros2 launch a2_ros sim.launch.py scene:=scene_maze.xml rviz:=$RVIZ dlio:=$DLIO
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
  --init)
    if ! command -v terminator &>/dev/null; then
        echo "Error: terminator is not installed. Install with: sudo apt install terminator"
        exit 1
    fi
    D=$(mktemp -d /tmp/a2_init_XXXX)

    # Each init file sources .bashrc then uses the CPR trick to pre-fill the
    # readline prompt with the command (visible and editable, not yet executed).
    cat > "$D/1.sh" << 'INITEOF'
source "$HOME/.bashrc"
_p() { bind '"\e[0n": "a2 --start"'; printf '\033[5n'; PROMPT_COMMAND=; }
PROMPT_COMMAND=_p
INITEOF
    cat > "$D/2.sh" << 'INITEOF'
source "$HOME/.bashrc"
_p() { bind '"\e[0n": "a2 --walk"'; printf '\033[5n'; PROMPT_COMMAND=; }
PROMPT_COMMAND=_p
INITEOF
    cat > "$D/3.sh" << 'INITEOF'
source "$HOME/.bashrc"
_p() { bind '"\e[0n": "a2 --nav"'; printf '\033[5n'; PROMPT_COMMAND=; }
PROMPT_COMMAND=_p
INITEOF
    cat > "$D/4.sh" << 'INITEOF'
source "$HOME/.bashrc"
_p() { bind '"\e[0n": "a2 --source"'; printf '\033[5n'; PROMPT_COMMAND=; }
PROMPT_COMMAND=_p
INITEOF

    cat > "$D/t.cfg" << EOF
[global_config]
[keybindings]
[profiles]
  [[default]]
  [[a2_start]]
    background_color = "#0d1f0d"
    use_theme_colors = False
  [[a2_walk]]
    background_color = "#0d0d1f"
    use_theme_colors = False
  [[a2_nav]]
    background_color = "#1f0d0d"
    use_theme_colors = False
  [[a2_source]]
    background_color = "#1a150d"
    use_theme_colors = False
[layouts]
  [[a2]]
    [[[window0]]]
      type = Window
      parent = ""
    [[[hpane]]]
      type = HPaned
      parent = window0
      ratio = 0.5
    [[[vpane_left]]]
      type = VPaned
      parent = hpane
      ratio = 0.5
    [[[t_start]]]
      type = Terminal
      parent = vpane_left
      command = bash --init-file $D/1.sh
      profile = a2_start
    [[[t_walk]]]
      type = Terminal
      parent = vpane_left
      command = bash --init-file $D/2.sh
      profile = a2_walk
    [[[vpane_right]]]
      type = VPaned
      parent = hpane
      ratio = 0.5
    [[[t_nav]]]
      type = Terminal
      parent = vpane_right
      command = bash --init-file $D/3.sh
      profile = a2_nav
    [[[t_source]]]
      type = Terminal
      parent = vpane_right
      command = bash --init-file $D/4.sh
      profile = a2_source
[plugins]
EOF
    terminator --no-dbus -g "$D/t.cfg" -l a2 &
    ;;
  *)
    echo "Usage: $0 {--start|--walk|--nav|--exploration|--dlio|--source|--bashrc|--init} [--rviz]"
    echo ""
    echo "  --start        Launch the MuJoCo simulation"
    echo "  --walk         Command the robot to walk (publishes mode=3)"
    echo "  --nav          Launch the navigation stack"
    echo "  --exploration  Launch autonomous exploration (TARE)"
    echo "  --dlio         Launch DLIO LiDAR-inertial odometry"
    echo "  --source       Source the workspace setup"
    echo "  --bashrc       Add the 'a2' shell function to ~/.bashrc"
    echo "  --init         Open a 4-pane terminator window pre-filled with common commands"
    echo "  --rviz         Open RViz alongside the launch"
    exit 1
    ;;
esac
