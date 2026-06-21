"""
PC2 launch.

Starts:
  - a2_unitree_bridge  : bridge node (publishes /joint_states and /imu/data from hardware)
  - joy_node           : reads gamepad from /dev/input/js0
  - teleop_joy         : maps gamepad axes/buttons to /joy_vel (via twist_mux) and /a2/mode (FSM)
  - gscam2             : H.264 multicast camera stream

Usage:
  ros2 launch a2_pc2 pc2.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    bridge_launch_dir = get_package_share_directory('a2_unitree_bridge')
    a2_pc2_launch_dir = os.path.join(get_package_share_directory('a2_pc2'), 'launch')
    a2_description_dir = get_package_share_directory('a2_description')

    a2_ros_config_dir = os.path.join(get_package_share_directory('a2_ros'), 'config')

    bridge_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bridge_launch_dir, 'launch', 'robot.launch.py')
        )
    )

    # Joy Node runs as a separate docker service on the PC2
    # to allow for spawn up and down based on bluetooth connection
    # joy_node = Node(
    #     package='joy',
    #     executable='joy_node',
    #     name='joy_node',
    #     parameters=[{
    #         'deadzone': 0.05,
    #         'autorepeat_rate': 1000.0,
    #     }]
    # )

    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        name='twist_mux',
        output='screen',
            remappings={('/cmd_vel_out', '/cmd_vel')},
        parameters=[
            os.path.join(a2_ros_config_dir, 'twist_mux_config.yaml'),
            {'use_sim_time': False},
        ]
    )

    teleop_node = Node(
        package='a2_pc2',
        executable='teleop_joy',
        output='screen',
        parameters=[{
            'linear_x_limit':  1.5,
            'linear_y_limit':  1.0,
            'angular_z_limit': 2.0,
        }]
    )

    camera_info_url = (
        'file://' + os.path.join(a2_description_dir, 'config', 'camera_info.yaml')
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(a2_pc2_launch_dir, 'camera.launch.py')
        ),
        launch_arguments={'camera_info_url': camera_info_url}.items(),
    )

    return LaunchDescription([
        bridge_launch,
        # joy_node,
        twist_mux_node,
        teleop_node,
        camera_launch,
    ])
