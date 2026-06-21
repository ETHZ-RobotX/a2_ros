"""
Full A2 real-robot launch.

Starts:
  - a2_unitree_bridge  : bridge node (publishes /joint_states and /imu/data from hardware)
  - hesai_ros_driver   : Hesai LiDAR driver (front lidar by default)
  - joy_node           : reads gamepad from /dev/input/js0
  - teleop_joy         : maps gamepad axes/buttons to /joy_vel (via twist_mux) and /a2/mode
  - gscam2             : H.264 multicast camera stream

Always on:
  - robot_state_publisher : broadcasts fixed TF links from URDF

Optional (pass rviz:=true):
  - rviz2 : 3-D visualisation

Usage:
  ros2 launch a2_ros real.launch.py
  ros2 launch a2_ros real.launch.py rviz:=true
  ros2 launch a2_ros real.launch.py lidar_config:=config_rear.yaml
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    PopLaunchConfigurations,
    PushLaunchConfigurations,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    description_dir = get_package_share_directory('a2_description')
    bridge_launch_dir = get_package_share_directory('a2_unitree_bridge')
    a2_ros_launch_dir = os.path.join(get_package_share_directory('a2_ros'), 'launch')
    hesai_launch_dir = os.path.join(get_package_share_directory('hesai_ros_driver'), 'launch')

    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='false',
        description='Launch RViz2 visualisation'
    )

    lidar_config_arg = DeclareLaunchArgument(
        'lidar_config',
        default_value='config_front.yaml',
        description='Hesai config filename (relative to hesai_ros_driver/config/)'
    )

    a2_ros_dir = get_package_share_directory('a2_ros')
    urdf_path = os.path.join(description_dir, 'urdf', 'a2.urdf')
    rviz_path = os.path.join(a2_ros_dir, 'rviz', 'robot.rviz')

    bridge_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bridge_launch_dir, 'launch', 'robot.launch.py')
        )
    )

    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(a2_ros_launch_dir, 'teleop_joy.launch.py')
        )
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(a2_ros_launch_dir, 'camera.launch.py')
        )
    )

    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(hesai_launch_dir, 'start_launch.py')
        ),
        launch_arguments={
            'config_file': LaunchConfiguration('lidar_config'),
            'rviz': 'false',
        }.items()
    )

    robot_state_pub_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': ParameterValue(
                Command(['cat ', urdf_path]), value_type=str
            ),
            'use_sim_time': False,
        }],
    )

    #IMU sits at [8.62, -9.14, -39.16] mm relative to the lidar frame.
    front_imu_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='front_lidar_imu_tf',
        arguments=[
            '--x', '0.00862', '--y', '-0.00914', '--z', '-0.03916',
            '--frame-id', 'front_lidar_link', '--child-frame-id', 'front_imu_link',
        ],
    )

    rear_imu_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='rear_lidar_imu_tf',
        arguments=[
            '--x', '0.00862', '--y', '-0.00914', '--z', '-0.03916',
            '--frame-id', 'rear_lidar_link', '--child-frame-id', 'rear_imu_link',
        ],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_path],
        parameters=[{'use_sim_time': False}],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    return LaunchDescription([
        rviz_arg,
        lidar_config_arg,
        # bridge_launch,
        # teleop_launch,
        # camera_launch,
        # Scope the 'rviz':'false' override below to lidar_launch only -
        # without push/pop it overwrites the global 'rviz' LaunchConfiguration,
        # which also suppresses the rviz_node below.
        
        PushLaunchConfigurations(),
        lidar_launch,
        PopLaunchConfigurations(),

        robot_state_pub_node,
        front_imu_tf_node,
        rear_imu_tf_node,
        rviz_node,
    ])
