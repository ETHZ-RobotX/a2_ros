#!/bin/bash

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"

# Load .env from workspace root (silently — values can be overridden by the caller's environment)
if [ -f "$WORKSPACE_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$WORKSPACE_DIR/.env"
    set +a
fi
