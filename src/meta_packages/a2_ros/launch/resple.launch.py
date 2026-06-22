"""
RESPLE launch for the A2 robot — all parameters live in
config/resple/params_a2.yaml (no dependency on the resple package config).

Remaps resple outputs to the topics the CMU autonomy stack expects:
  - Mapping/odometry    -> /state_estimation
  - RESPLE/current_scan -> /registered_scan
  - static TF: world    -> map  (identity)

Usage:
  ros2 launch a2_ros resple.launch.py
  ros2 launch a2_ros resple.launch.py rviz:=true
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    a2_ros_dir = get_package_share_directory('a2_ros')

    a2_params = os.path.join(a2_ros_dir, 'config', 'resple', 'params_a2.yaml')
    rviz_config = os.path.join(a2_ros_dir, 'rviz', 'resple.rviz')

    rviz = LaunchConfiguration('rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_saving_node = LaunchConfiguration('map_saving_node')

    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='false', description='Launch RViz2'),
        DeclareLaunchArgument('use_sim_time', default_value='false', description='Use simulation time'),
        DeclareLaunchArgument('map_saving_node', default_value='false', description='Launch the MapSaving node'),

        Node(
            package='resple',
            executable='RESPLE',
            name='RESPLE',
            emulate_tty=True,
            output='both',
            parameters=[a2_params, {'use_sim_time': ParameterValue(use_sim_time, value_type=bool)}],
            arguments=['--ros-args', '--log-level', 'INFO'],
        ),

        Node(
            package='resple',
            executable='Mapping',
            name='Mapping',
            emulate_tty=True,
            output='both',
            parameters=[a2_params, {'use_sim_time': ParameterValue(use_sim_time, value_type=bool)}],
            arguments=['--ros-args', '--log-level', 'INFO'],
        ),

        Node(
            package='resple',
            executable='MapSaving',
            name='MapSaving',
            emulate_tty=True,
            output='both',
            parameters=[a2_params, {'use_sim_time': ParameterValue(use_sim_time, value_type=bool)}],
            arguments=['--ros-args', '--log-level', 'INFO'],
            condition=IfCondition(map_saving_node),
        ),

        # Planners expect the "map" frame; RESPLE uses "world".
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='world_to_map_tf',
            arguments=['0', '0', '0', '0', '0', '0', 'world', 'map'],
            parameters=[{'use_sim_time': ParameterValue(use_sim_time, value_type=bool)}],
        ),

        # RESPLE "body" is the IMU/lidar frame, rotated relative to the robot.
        # Connects resple TF tree (world -> body) to URDF tree (base_link -> ...).
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='body_to_base_link_tf',
            arguments=['0', '-0.08134', '-0.33767',
                        '-1.5708', '-1.5708', '0',
                        'body', 'base_link'],
            parameters=[{'use_sim_time': ParameterValue(use_sim_time, value_type=bool)}],
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config, '--ros-args', '--log-level', 'WARN'],
            condition=IfCondition(rviz),
            parameters=[{'use_sim_time': ParameterValue(use_sim_time, value_type=bool)}],
        ),
    ])
