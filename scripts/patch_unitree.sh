#!/bin/bash
set -e

# Source common
source ./scripts/common.sh

info "Patching unitree message packages for Jazzy..."
UNITREE_MSG_ROOT="$WORKSPACE_DIR/external/unitree_ros2/cyclonedds_ws/src/unitree"
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
