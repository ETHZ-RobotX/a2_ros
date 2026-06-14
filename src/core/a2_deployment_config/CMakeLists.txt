cmake_minimum_required(VERSION 3.8)
project(a2_deployment_config)

find_package(ament_cmake REQUIRED)

# This package installs only config files and scripts (no build targets).
# colcon passes catkin-compatibility cache variables that a pure-ament package
# never reads, which triggers CMake's "Manually-specified variables were not
# used" warning. Reference them here so CMake marks them as used and stays quiet.
set(_a2_ignored_vars "${CATKIN_INSTALL_INTO_PREFIX_ROOT}${CATKIN_SYMLINK_INSTALL}")

install(
  DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    scripts/render_zenoh_config.py
    scripts/setup_zenoh.sh
    scripts/setup_cyclonedds.sh
  DESTINATION share/${PROJECT_NAME}/scripts
)

ament_package()
