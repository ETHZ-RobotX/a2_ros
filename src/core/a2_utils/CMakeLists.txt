cmake_minimum_required(VERSION 3.16)
project(a2_utils)

set(DEPENDENCY_LIST
  rclcpp
  sensor_msgs
  tf2_ros
  tf2
  tf2_sensor_msgs
)

find_package(ament_cmake REQUIRED)
foreach(dep ${DEPENDENCY_LIST})
  find_package(${dep} REQUIRED)
endforeach()

add_executable(registered_scan_pub src/registered_scan_pub.cpp)
ament_target_dependencies(registered_scan_pub ${DEPENDENCY_LIST})

install(TARGETS
  registered_scan_pub
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
