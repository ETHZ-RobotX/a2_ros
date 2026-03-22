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
MUJOCO_VERSION="3.5.0"
MUJOCO_DIR="$HOME/.mujoco/mujoco-${MUJOCO_VERSION}"

echo "=== a2_ros install ==="
echo "Repo      : $SCRIPT_DIR"
echo "MuJoCo    : ${MUJOCO_VERSION}"
echo ""

# ---------------------------------------------------------------
# Conda guard — ROS2 build must use system Python, not conda
# ---------------------------------------------------------------
if [ -n "$CONDA_PREFIX" ]; then
    warn "Conda is active (env: ${CONDA_DEFAULT_ENV:-base})."
    warn "ROS2 colcon build requires system Python 3.12 — conda Python breaks the build."
    error "Aborting. Run 'conda deactivate' (repeat if in a named env) then re-run install.sh."
    exit 1
fi

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
    build-essential cmake git wget python3.12-venv
    ros-jazzy-joy ros-jazzy-robot-state-publisher ros-jazzy-rviz2
    ros-jazzy-rmw-cyclonedds-cpp
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

# empy 3.3.4 is required by ROS2 at build time (system Python, not venv)
if ! /usr/bin/python3 -c "import em" 2>/dev/null; then
    info "Installing empy for system Python..."
    sudo /usr/bin/python3 -m pip install --break-system-packages "empy==3.3.4"
else
    info "empy already installed for system Python."
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
# Ignore unitree_ros2 example package (not needed, would fail to build)
# ---------------------------------------------------------------
touch "$SCRIPT_DIR/external/unitree_ros2/example/COLCON_IGNORE"

# ---------------------------------------------------------------
# Patch unitree message packages for ROS2 Jazzy
# The upstream unitree_ros2 repo targets Foxy and uses rosidl_generator_dds_idl
# which was removed in later ROS2 versions. Strip the three Foxy-only blocks.
# ---------------------------------------------------------------
info "Patching unitree message packages for Jazzy..."
UNITREE_MSG_ROOT="$SCRIPT_DIR/external/unitree_ros2/cyclonedds_ws/src/unitree"
for PKG in unitree_go unitree_hg unitree_api; do
    CMAKE="$UNITREE_MSG_ROOT/$PKG/CMakeLists.txt"
    [ -f "$CMAKE" ] || continue
    if ! grep -q "rosidl_generator_dds_idl" "$CMAKE"; then
        info "  $PKG: already patched"
        continue
    fi
    python3 - "$CMAKE" <<'PYEOF'
import re, sys
path = sys.argv[1]
txt = open(path).read()
# Remove: find_package(rosidl_generator_dds_idl REQUIRED)
txt = re.sub(r'find_package\(rosidl_generator_dds_idl[^\n]*\n', '', txt)
# Remove: rosidl_generate_dds_interfaces(...) block
txt = re.sub(r'\nrosidl_generate_dds_interfaces\(.*?\)', '', txt, flags=re.DOTALL)
# Remove: add_dependencies(...dds_connext_idl...) block
txt = re.sub(r'\nadd_dependencies\(\s*\$\{PROJECT_NAME\}\s*\$\{PROJECT_NAME\}__dds_connext_idl\s*\)', '', txt, flags=re.DOTALL)
open(path, 'w').write(txt)
PYEOF
    info "  $PKG: patched"
done

# ---------------------------------------------------------------
# Python venv
# --system-site-packages lets the venv see ROS2 Python packages
# (rclpy, etc.) without needing to install them again.
# We never *activate* the venv here so colcon uses system Python.
# ---------------------------------------------------------------
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    info "Creating Python venv at .venv (--system-site-packages)..."
    /usr/bin/python3 -m venv --system-site-packages "$VENV_DIR"
else
    info "Python venv already exists."
fi

info "Checking Python packages in venv..."
"$VENV_DIR/bin/python3" -c "import torch" 2>/dev/null \
    && info "  torch already installed." \
    || { info "  Installing torch (this may take a while — ~700 MB)..."; "$VENV_DIR/bin/pip" install torch; }
"$VENV_DIR/bin/python3" -c "import numpy" 2>/dev/null \
    && info "  numpy already installed." \
    || { info "  Installing numpy..."; "$VENV_DIR/bin/pip" install numpy --quiet; }

# ---------------------------------------------------------------
# Build workspace (builds inside the repo directory)
# Venv must NOT be active here — colcon needs system Python.
# ---------------------------------------------------------------
info "Building workspace..."
source /opt/ros/jazzy/setup.bash
cd "$SCRIPT_DIR"
# a2_mujoco uses /proc/self/exe to locate its install prefix, so its binary
# must be physically copied (not symlinked) — build it separately without --symlink-install.
colcon build --symlink-install --packages-skip a2_mujoco
colcon build --packages-select a2_mujoco
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
