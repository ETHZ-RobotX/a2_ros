#!/bin/bash
set -e

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

ask_yn() {
    while true; do
        read -rp "$1 [y/n]: " yn
        case $yn in [Yy]*) return 0;; [Nn]*) return 1;; *) echo "Answer y or n.";; esac
    done
}

SCRIPT_DIR=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
WS_ROOT=$(realpath "$SCRIPT_DIR/../../..")
MUJOCO_VERSION="3.3.6"
MUJOCO_DIR="$HOME/.mujoco/mujoco-${MUJOCO_VERSION}"

echo "=== a2_ros install ==="
echo "Workspace : $WS_ROOT"
echo "MuJoCo    : ${MUJOCO_VERSION}"
echo ""

# ---------------------------------------------------------------
# Submodules
# ---------------------------------------------------------------
info "Initialising git submodules..."
# a2_mujoco needs the mujoco symlink removed before git can clone into it
MUJOCO_SYMLINK="$SCRIPT_DIR/external/a2_mujoco/mujoco"
[ -L "$MUJOCO_SYMLINK" ] && rm "$MUJOCO_SYMLINK"
git -C "$SCRIPT_DIR" submodule update --init --recursive

# ---------------------------------------------------------------
# System packages
# ---------------------------------------------------------------
info "Checking system packages..."
PKGS=(
    build-essential cmake git wget
    ros-jazzy-joy ros-jazzy-robot-state-publisher ros-jazzy-rviz2
    libyaml-cpp-dev libspdlog-dev libboost-all-dev libfmt-dev libglfw3-dev
)
MISSING=()
for pkg in "${PKGS[@]}"; do
    dpkg -s "$pkg" &>/dev/null || MISSING+=("$pkg")
done
if [ ${#MISSING[@]} -gt 0 ]; then
    info "Installing: ${MISSING[*]}"
    sudo apt-get install -y "${MISSING[@]}"
else
    info "All system packages present."
fi

# ---------------------------------------------------------------
# MuJoCo
# ---------------------------------------------------------------
info "Checking MuJoCo..."

# Warn about other installed versions
if [ -d "$HOME/.mujoco" ]; then
    for dir in "$HOME"/.mujoco/mujoco-*; do
        [ -d "$dir" ] || continue
        [ "$dir" = "$MUJOCO_DIR" ] && continue
        warn "Found different MuJoCo version: $dir"
        if ask_yn "Remove $(basename "$dir") and replace with ${MUJOCO_VERSION}?"; then
            rm -rf "$dir"
        else
            error "Aborting. Remove conflicting version manually or update MUJOCO_VERSION."
            exit 1
        fi
    done
fi

if [ ! -d "$MUJOCO_DIR" ]; then
    info "Downloading MuJoCo ${MUJOCO_VERSION}..."
    mkdir -p "$HOME/.mujoco"
    TMP=$(mktemp -d)
    wget -q --show-progress \
        "https://github.com/google-deepmind/mujoco/releases/download/${MUJOCO_VERSION}/mujoco-${MUJOCO_VERSION}-linux-x86_64.tar.gz" \
        -O "$TMP/mujoco.tar.gz"
    tar -xzf "$TMP/mujoco.tar.gz" -C "$HOME/.mujoco/"
    rm -rf "$TMP"
    info "MuJoCo installed to $MUJOCO_DIR"
else
    info "MuJoCo ${MUJOCO_VERSION} already present."
fi

# Fix symlink in a2_mujoco
SYMLINK="$SCRIPT_DIR/external/a2_mujoco/mujoco"
rm -f "$SYMLINK"
ln -s "$MUJOCO_DIR" "$SYMLINK"
info "Symlink: external/a2_mujoco/mujoco -> $MUJOCO_DIR"

# ---------------------------------------------------------------
# Unitree SDK2
# ---------------------------------------------------------------
info "Checking Unitree SDK2..."
if [ -d "/opt/unitree_robotics" ]; then
    info "Unitree SDK2 already installed at /opt/unitree_robotics."
    if ask_yn "Reinstall Unitree SDK2?"; then
        sudo rm -rf /opt/unitree_robotics
    fi
fi

if [ ! -d "/opt/unitree_robotics" ]; then
    info "Installing Unitree SDK2..."
    TMP=$(mktemp -d)
    git clone --depth=1 https://github.com/unitreerobotics/unitree_sdk2.git "$TMP/unitree_sdk2"
    cmake -S "$TMP/unitree_sdk2" -B "$TMP/unitree_sdk2/build" \
          -DCMAKE_INSTALL_PREFIX=/opt/unitree_robotics
    sudo cmake --build "$TMP/unitree_sdk2/build" --target install -- -j"$(nproc)"
    rm -rf "$TMP"
    info "Unitree SDK2 installed to /opt/unitree_robotics"
fi

# ---------------------------------------------------------------
# Python packages
# ---------------------------------------------------------------
info "Checking Python packages..."
python3 -c "import torch" 2>/dev/null  && info "torch already installed."  || { info "Installing torch...";  pip install torch  --quiet; }
python3 -c "import numpy" 2>/dev/null  && info "numpy already installed."  || { info "Installing numpy...";  pip install numpy  --quiet; }

# ---------------------------------------------------------------
# Ignore old/stale workspaces in the same src/ tree
# ---------------------------------------------------------------
for ignore_candidate in "$WS_ROOT/src/rss_simulation_ws" "$WS_ROOT/src/rss_ws"; do
    if [ -d "$ignore_candidate" ] && [ ! -f "$ignore_candidate/COLCON_IGNORE" ]; then
        touch "$ignore_candidate/COLCON_IGNORE"
        info "Added COLCON_IGNORE to $ignore_candidate"
    fi
done

# ---------------------------------------------------------------
# Build workspace
# ---------------------------------------------------------------
info "Building workspace..."
source /opt/ros/jazzy/setup.bash
cd "$WS_ROOT"
colcon build --symlink-install
info "Build complete."

# ---------------------------------------------------------------
# Verify: open MuJoCo viewer
# ---------------------------------------------------------------
echo ""
info "Verifying MuJoCo installation..."

SIMULATE="$MUJOCO_DIR/bin/simulate"
SAMPLE_MODEL=$(find "$MUJOCO_DIR/model" -name "*.xml" | head -1)

if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    info "Display detected. Opening MuJoCo viewer (close the window to finish)..."
    "$SIMULATE" "$SAMPLE_MODEL"
    info "MuJoCo opened successfully — installation verified."
else
    info "Headless environment. Checking MuJoCo library..."
    python3 - <<EOF
import ctypes, sys
try:
    ctypes.cdll.LoadLibrary("$MUJOCO_DIR/lib/libmujoco.so.${MUJOCO_VERSION}")
    print("  MuJoCo library loads correctly.")
except OSError as e:
    print(f"  ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF
fi

# ---------------------------------------------------------------
echo ""
info "Done. In each new terminal run:"
echo "    source $SCRIPT_DIR/setup.sh"
