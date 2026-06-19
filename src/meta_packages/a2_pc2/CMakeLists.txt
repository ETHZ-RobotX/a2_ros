cmake_minimum_required(VERSION 3.8)
project(a2_pc2)

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
find_package(a2_interfaces REQUIRED)

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

install(TARGETS
  teleop_joy
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
