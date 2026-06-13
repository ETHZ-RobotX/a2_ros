cmake_minimum_required(VERSION 3.8)
project(a2_deployment_config)

find_package(ament_cmake REQUIRED)

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
