"""
Full A2 simulation launch.

Starts:
  - a2_mujoco       : MuJoCo physics simulator (publishes /lowstate, subscribes /lowcmd)
  - locomotion_controller : RL policy node (subscribes /lowstate + /mode + /cmd_vel,
                                             publishes /lowcmd)
  - joy_node        : reads gamepad from /dev/input/js0
  - teleop_joy      : maps gamepad axes/buttons to /cmd_vel and /mode

Optional (pass rviz:=true):
  - sim_clock_node  : publishes /clock from sim time
  - robot_state_publisher : broadcasts TF from URDF
  - rviz2           : 3-D visualisation

Usage:
  ros2 launch a2_sim sim.launch.py
  ros2 launch a2_sim sim.launch.py rviz:=true
  ros2 launch a2_sim sim.launch.py scene:=scene_terrain.xml
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    description_dir = get_package_share_directory('a2_description')
    mujoco_dir      = get_package_share_directory('a2_mujoco')

    # ---------- launch arguments ----------
    scene_arg = DeclareLaunchArgument(
        'scene',
        default_value='scene.xml',
        description='Scene XML filename inside share/a2_description/mjcf/'
    )
    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='false',
        description='Launch RViz2 visualisation'
    )

    scene_path = PathJoinSubstitution([description_dir, 'mjcf', LaunchConfiguration('scene')])
    mjcf_dir   = os.path.join(description_dir, 'mjcf')
    urdf_path  = os.path.join(description_dir, 'urdf', 'a2.urdf')
    rviz_path  = os.path.join(description_dir, 'rviz', 'default.rviz')

    # ---------- nodes ----------
    mujoco_node = Node(
        package='a2_mujoco',
        executable='a2_mujoco',
        output='screen',
        arguments=[scene_path, mujoco_dir],
        # MuJoCo resolves mesh paths relative to CWD
        cwd=mjcf_dir,
    )

    locomotion_node = Node(
        package='a2_locomotion_controller',
        executable='a2_locomotion_controller.py',
        output='screen',
        parameters=[{'use_sim_time': True}],
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

    # --- optional visualisation ---
    sim_clock_node = Node(
        package='a2_description',
        executable='sim_clock_node',
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    robot_state_pub_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': ParameterValue(
                Command(['cat ', urdf_path]), value_type=str
            ),
            'use_sim_time': True,
        }],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_path],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    return LaunchDescription([
        scene_arg,
        rviz_arg,
        mujoco_node,
        locomotion_node,
        joy_node,
        teleop_node,
        sim_clock_node,
        robot_state_pub_node,
        rviz_node,
    ])
