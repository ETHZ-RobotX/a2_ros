#!/usr/bin/env bash
#
# Installs KasmVNC + a minimal Openbox window manager, so GUI tools (RViz, the
# joint_state_publisher GUI, etc.) can be viewed in a browser on hosts without
# native X11 (macOS / Windows).
#
# Adapted from smb_ros2_workspace's scripts/setup/setup-kasmvnc.sh, deliberately
# trimmed for a smaller, safer footprint:
#   - a minimal Openbox WM instead of a full MATE desktop (~tens of MB vs ~1 GB)
#   - a pinned KasmVNC version and an architecture-matched .deb (amd64 / arm64)
#   - an optional sha256 integrity check (set KASMVNC_SHA256 to enforce)
#   - apt lists cleaned in-layer
#
# Run as root (it installs apt packages). Designed to run at Docker build time.
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
    echo "ERROR: setup-kasmvnc.sh must run as root (it installs apt packages)." >&2
    exit 1
fi

KASMVNC_VERSION="${KASMVNC_VERSION:-1.3.4}"

# Ubuntu codename (e.g. 'noble') — KasmVNC ships codename-specific .debs.
# shellcheck disable=SC1091
source /etc/os-release
CODENAME="${VERSION_CODENAME:?could not read VERSION_CODENAME from /etc/os-release}"

# Architecture-matched asset (KasmVNC uses amd64 / arm64 in its .deb names).
case "$(uname -m)" in
    x86_64)        ARCH=amd64 ;;
    aarch64|arm64) ARCH=arm64 ;;
    *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

DEB_URL="https://github.com/kasmtech/KasmVNC/releases/download/v${KASMVNC_VERSION}/kasmvncserver_${CODENAME}_${KASMVNC_VERSION}_${ARCH}.deb"
DEB_PATH="/tmp/kasmvncserver.deb"

echo "[kasmvnc] Downloading ${DEB_URL}"
wget -qO "${DEB_PATH}" "${DEB_URL}"

# Optional integrity check. Export KASMVNC_SHA256 to enforce it.
if [[ -n "${KASMVNC_SHA256:-}" ]]; then
    echo "[kasmvnc] Verifying sha256"
    echo "${KASMVNC_SHA256}  ${DEB_PATH}" | sha256sum -c -
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
# KasmVNC server + a standard XFCE desktop. XFCE bundles its own window manager
# (xfwm4), panel, desktop, and Thunar file manager as hard dependencies, so it
# comes up as a complete, polished desktop with no missing-WM surprises — while
# staying lighter than MATE/GNOME. We skip xfce4-goodies to avoid bloat.
# Supporting bits:
#   xfce4-terminal  - the desktop terminal (a Recommends of xfce4, so listed
#                     explicitly under --no-install-recommends)
#   dbus-x11        - Qt/RViz/XFCE expect a session DBus
#   ssl-cert        - provides the "snakeoil" cert/key KasmVNC needs even in HTTP
#                     mode (the smb script got this transitively from MATE)
#   x11-xserver-utils - xrandr etc. used by the session
apt-get install -y --no-install-recommends \
    "${DEB_PATH}" \
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    ssl-cert \
    x11-xserver-utils

# Generate the snakeoil cert explicitly (in case the package postinst didn't).
make-ssl-cert generate-default-snakeoil --force-overwrite

rm -f "${DEB_PATH}"
rm -rf /var/lib/apt/lists/*

echo "[kasmvnc] Installed KasmVNC ${KASMVNC_VERSION} (${CODENAME}/${ARCH}) + Openbox"
