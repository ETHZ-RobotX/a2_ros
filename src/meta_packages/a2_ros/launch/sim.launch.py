"""
Full A2 simulation launch.

Starts:
  - a2_mujoco            : MuJoCo physics simulator (publishes /lowstate, subscribes /lowcmd)
  - locomotion_controller: RL policy node (subscribes /lowstate + /mode + /cmd_vel,
                                            publishes /lowcmd)
  - a2_bridge            : republishes /lowstate as /joint_states, /imu/data, /odom, /state_estimation; broadcasts TF
  - registered_scan_pub  : transforms /mujoco/front_lidar into map frame → /registered_scan
  - joy_node             : reads gamepad from /dev/input/js0
  - teleop_joy           : maps gamepad axes/buttons to /cmd_vel and /mode

Arguments:
  dlio:=false  (default) — a2_bridge broadcasts ground-truth map→base_link TF.
  dlio:=true             — a2_bridge does NOT broadcast TF; DLIO (launched separately
                           via `a2 --dlio`) provides it instead. registered_scan_pub
                           will fail TF lookups until DLIO is up, then work normally.

Optional (pass rviz:=true):
  - robot_state_publisher: broadcasts TF from URDF
  - rviz2                : 3-D visualisation

Usage:
  ros2 launch a2_ros sim.launch.py
  ros2 launch a2_ros sim.launch.py dlio:=true
  ros2 launch a2_ros sim.launch.py rviz:=true scene:=scene_terrain.xml
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    description_dir = get_package_share_directory('a2_description')

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
    dlio_arg = DeclareLaunchArgument(
        'dlio',
        default_value='false',
        description='Use DLIO for odometry instead of ground-truth TF from a2_bridge. '
                    'Run `a2 --dlio` in a separate terminal when using this flag.'
    )

    scene_path = PathJoinSubstitution([description_dir, 'mjcf', LaunchConfiguration('scene')])
    mjcf_dir   = os.path.join(description_dir, 'mjcf')
    urdf_path  = os.path.join(description_dir, 'urdf', 'a2.urdf')
    rviz_path  = os.path.join(description_dir, 'rviz', 'default.rviz')

    dlio = LaunchConfiguration('dlio')

    # ---------- nodes ----------
    mujoco_node = Node(
        package='unitree_mujoco',
        executable='unitree_mujoco',
        output='screen',
        arguments=['-s', scene_path],
        cwd=mjcf_dir,
    )

    locomotion_node = Node(
        package='a2_locomotion_controller',
        executable='locomotion_executor',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    # sim_clock_node = Node(
    #     package='a2_sim_utils',
    #     executable='sim_clock',
    #     output='screen',
    #     parameters=[{'use_sim_time': False}],
    # )

    a2_bridge_node = Node(
        package='a2_unitree_bridge',
        executable='a2_bridge_sim',
        output='screen',
        parameters=[{'use_sim_time': True, 'publish_tf': True}],
        condition=UnlessCondition(dlio),
    )

    # DLIO mode: a2_bridge skips TF broadcast (DLIO provides it)
    a2_bridge_dlio = Node(
        package='a2_sim_utils',
        executable='a2_bridge',
        output='screen',
        parameters=[{'use_sim_time': True, 'publish_tf': False}],
        condition=IfCondition(dlio),
    )

    # Transforms raw LiDAR into map frame → /registered_scan.
    # Works regardless of TF source (ground-truth or DLIO).
    registered_scan_node = Node(
        package='a2_utils',
        executable='registered_scan_pub',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'input_topic':  '/mujoco/front_lidar',
            'target_frame': 'map',
            'tf_lag_sec':   0.025,
        }],
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

    # Always on — needed for TF chain base_link→lidar/imu
    robot_state_pub_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': ParameterValue(
                Command(['cat ', urdf_path]), value_type=str
            ),
            'use_sim_time': True,
        }],
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
        dlio_arg,
        mujoco_node,
        locomotion_node,
        a2_bridge_node,
        a2_bridge_dlio,
        registered_scan_node,
        joy_node,
        teleop_node,
        robot_state_pub_node,
        rviz_node,
    ])
