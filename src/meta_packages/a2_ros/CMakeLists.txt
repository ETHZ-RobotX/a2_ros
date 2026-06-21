cmake_minimum_required(VERSION 3.8)
project(a2_ros)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

include_directories(include)

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(unitree_go REQUIRED)
find_package(unitree_hg REQUIRED)
find_package(unitree_api REQUIRED)
find_package(rosbag2_cpp REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(a2_interfaces REQUIRED)

# stand_example node (low-level stand/sit transitions)
add_executable(stand_example
  src/stand_example.cpp
  src/motor_crc.cpp
)
target_compile_features(stand_example PRIVATE cxx_std_20)
ament_target_dependencies(stand_example
  rclcpp
  std_msgs
  unitree_go
  unitree_hg
  unitree_api
  rosbag2_cpp
)

# teleop_joy node (joystick teleoperation)
add_executable(teleop_joy
  src/teleop_joy.cpp
)
ament_target_dependencies(teleop_joy
  rclcpp
  geometry_msgs
  sensor_msgs
  a2_interfaces
)

add_executable(nav_vel_relay
  src/nav_vel_relay.cpp
)
ament_target_dependencies(nav_vel_relay
  rclcpp
  geometry_msgs
)

add_executable(scan_pose_sync
  src/scan_pose_sync.cpp
)
ament_target_dependencies(scan_pose_sync
  rclcpp
  nav_msgs
  sensor_msgs
  tf2
  tf2_ros
  geometry_msgs
)

add_executable(scripted_walk
  src/scripted_walk.cpp
)
ament_target_dependencies(scripted_walk
  rclcpp
  geometry_msgs
  a2_interfaces
)

install(TARGETS
  stand_example
  teleop_joy
  nav_vel_relay
  scan_pose_sync
  scripted_walk
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  config
  rviz
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
