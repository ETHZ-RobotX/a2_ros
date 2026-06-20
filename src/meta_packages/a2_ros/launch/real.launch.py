"""
Full A2 real-robot launch.

Starts:
  - locomotion_executor : RL policy node (subscribes /lowstate + /mode + /cmd_vel,
                                           publishes /lowcmd)
  - joint_states_pub    : republishes /lowstate motor positions as /joint_states
  - imu_pub             : republishes /lowstate IMU as /imu/data (needed by DLIO)
  - joy_node            : reads gamepad from /dev/input/js0
  - teleop_joy          : maps gamepad axes/buttons to /joy_vel (via twist_mux) and /a2/mode

Always on:
  - robot_state_publisher : broadcasts fixed TF links from URDF

Optional (pass rviz:=true):
  - rviz2 : 3-D visualisation

Usage:
  ros2 launch a2_ros real.launch.py
  ros2 launch a2_ros real.launch.py rviz:=true
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    description_dir = get_package_share_directory('a2_description')

    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='false',
        description='Launch RViz2 visualisation'
    )

    a2_ros_dir = get_package_share_directory('a2_ros')
    urdf_path = os.path.join(description_dir, 'urdf', 'a2.urdf')
    rviz_path = os.path.join(a2_ros_dir, 'rviz', 'default.rviz')

    locomotion_node = Node(
        package='a2_locomotion_controller',
        executable='locomotion_executor',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    joint_states_node = Node(
        package='a2_utils',
        executable='joint_states_pub',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    imu_node = Node(
        package='a2_utils',
        executable='imu_pub',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'dev': '/dev/input/js0',
            'deadzone': 0.05,
            'autorepeat_rate': 500.0,
        }]
    )

    teleop_node = Node(
        package='a2_ros',
        executable='teleop_joy',
        output='screen',
        parameters=[{
            'linear_speed_limit': 0.5,
            'angular_speed_limit': 1.0,
        }]
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

    # IMU sits at [8.62, -9.14, -39.16] mm relative to the lidar frame.
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
        # locomotion_node,
        joint_states_node,
        imu_node,
        # joy_node,
        # teleop_node,
        robot_state_pub_node,
        front_imu_tf_node,
        rear_imu_tf_node,
        rviz_node,
    ])
