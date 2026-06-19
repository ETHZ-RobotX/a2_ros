#!/bin/bash
set -e

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

# ---------------------------------------------------------------
# Build all Docker image stages with inline cache, then export
# them to a single gzipped tarball for offline distribution.
#
# Usage: ./scripts/export_images.sh [output_dir]
#   output_dir  where to write the tarball (default: ./dist)
# ---------------------------------------------------------------

OUTPUT_DIR="${1:-$WORKSPACE_DIR/dist}"
STAMP=$(date +"%Y%m%d_%H%M%S")
OUT="$OUTPUT_DIR/a2_ros_$STAMP.tar.gz"

mkdir -p "$OUTPUT_DIR"

# All images to include — order matters for docker save deduplication
IMAGES=(
    a2_ros:builder
    a2_ros:base
    a2_ros:dev
    a2_ros:robot
)

info "Building all stages with inline cache..."
(cd "$WORKSPACE_DIR" && docker compose --profile build build)

info "Saving images to: $OUT"
info "  ${IMAGES[*]}"
docker save "${IMAGES[@]}" | gzip > "$OUT"

SIZE=$(du -sh "$OUT" | cut -f1)
info "Done. Archive size: $SIZE"
info "To load on another machine: docker load < $OUT"
