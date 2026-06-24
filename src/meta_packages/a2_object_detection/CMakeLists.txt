cmake_minimum_required(VERSION 3.8)
project(a2_object_detection)
find_package(ament_cmake REQUIRED)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(message_filters REQUIRED)

# Install Python modules

# Install Python package directory (use existing folder)
install(DIRECTORY a2_object_detection
  DESTINATION lib/${PROJECT_NAME}
)

# Install Python executables
# install(PROGRAMS
#   a2_object_detection/artifact_memory_node.py
#   DESTINATION lib/${PROJECT_NAME}
# )

# Install launch files, config files, rviz files
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/launch")
  install(DIRECTORY launch DESTINATION share/${PROJECT_NAME}/launch)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/config")
  install(DIRECTORY config DESTINATION share/${PROJECT_NAME}/config)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/models")
  install(DIRECTORY models DESTINATION share/${PROJECT_NAME}/models)
endif()

ament_package()
