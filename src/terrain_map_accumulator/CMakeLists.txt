cmake_minimum_required(VERSION 3.8)
project(terrain_map_accumulator)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(PCL REQUIRED COMPONENTS common filters)

add_executable(terrain_map_accumulator src/terrain_map_accumulator.cpp)

ament_target_dependencies(terrain_map_accumulator
  rclcpp
  sensor_msgs
  pcl_conversions
)

# PCL isn't an ament package, so wire it in manually
target_include_directories(terrain_map_accumulator PRIVATE ${PCL_INCLUDE_DIRS})
target_link_libraries(terrain_map_accumulator ${PCL_LIBRARIES})
target_compile_definitions(terrain_map_accumulator PRIVATE ${PCL_DEFINITIONS})

install(TARGETS terrain_map_accumulator
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()