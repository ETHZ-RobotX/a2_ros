"""
PC2 launch.

Starts:
  - a2_unitree_bridge  : bridge node (publishes /joint_states and /imu/data from hardware)
  - gscam2             : H.264 multicast camera stream

Usage:
  ros2 launch a2_ros pc2.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    bridge_launch_dir = get_package_share_directory('a2_unitree_bridge')
    a2_ros_launch_dir = os.path.join(get_package_share_directory('a2_ros'), 'launch')

    bridge_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bridge_launch_dir, 'launch', 'robot.launch.py')
        )
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(a2_ros_launch_dir, 'camera.launch.py')
        )
    )

    return LaunchDescription([
        bridge_launch,
        camera_launch,
    ])
