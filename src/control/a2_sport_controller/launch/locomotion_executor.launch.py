"""
Launch the LocomotionExecutor node.

Usage:
  ros2 launch a2_locomotion_controller locomotion_executor.launch.py
"""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    locomotion_node = Node(
        package='a2_locomotion_controller',
        executable='locomotion_executor',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    return LaunchDescription([
        locomotion_node,
    ])
