"""
Full A2 simulation launch.

Starts:
  - a2_mujoco            : MuJoCo physics simulator (publishes /lowstate, subscribes /lowcmd)
  - locomotion_controller: RL policy node (subscribes /lowstate + /mode + /cmd_vel,
                                            publishes /lowcmd)
  - a2_bridge            : republishes /lowstate as /joint_states, /imu/data, /odom, /state_estimation;
                           transforms /front_lidar/points into map frame → /registered_scan; broadcasts TF
  - joy_node             : reads gamepad from /dev/input/js0
  - teleop_joy           : maps gamepad axes/buttons to /joy_vel (via twist_mux) and /a2/mode

Arguments:
  dlio:=false  (default) — a2_bridge broadcasts ground-truth map→base_link TF.
  dlio:=true             — a2_bridge publishes only IMU, joint_states, and camera;
                           odometry, TF, and registered_scan come from DLIO.
                           Launch DLIO separately in another terminal:
                             ros2 launch direct_lidar_inertial_odometry a2_front_live_rss.launch.py \
                               pointcloud_topic:=/front_lidar/points use_sim_time:=true

Optional (pass rviz:=true):
  - robot_state_publisher: broadcasts TF from URDF
  - rviz2                : 3-D visualisation

Usage:
  ros2 launch a2_ros sim.launch.py
  ros2 launch a2_ros sim.launch.py dlio:=true
  ros2 launch a2_ros sim.launch.py rviz:=true scene:=scene_terrain.xml
  ros2 launch a2_ros sim.launch.py headless:=true   # no MuJoCo viewer
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
    a2_ros_dir = get_package_share_directory('a2_ros')



    # ---------- launch arguments ----------
    scene_arg = DeclareLaunchArgument(
        'scene',
        default_value='scene_maze.xml',
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
    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Run MuJoCo with no viewer (no GUI/GL/display) — visualise in '
                    'RViz/Foxglove instead. Needs no X server / VNC.'
    )

    scene_path = PathJoinSubstitution([description_dir, 'mjcf', LaunchConfiguration('scene')])
    mjcf_dir   = os.path.join(description_dir, 'mjcf')
    urdf_path  = os.path.join(description_dir, 'urdf', 'a2.urdf')
    rviz_path  = os.path.join(a2_ros_dir, 'rviz', 'default.rviz')

    dlio = LaunchConfiguration('dlio')

    # ---------- nodes ----------
    mujoco_node = Node(
        package='unitree_mujoco',
        executable='unitree_mujoco',
        output='screen',
        arguments=['-s', scene_path],
        cwd=mjcf_dir,
        # The simulator reads UNITREE_MUJOCO_HEADLESS (accepts '1'/'true') to skip
        # the viewer entirely; pass the launch arg straight through.
        additional_env={'UNITREE_MUJOCO_HEADLESS': LaunchConfiguration('headless')},
    )

    locomotion_node = Node(
        package='a2_locomotion_controller',
        executable='locomotion_executor',
        output='screen',
        parameters=[{'use_sim_time': True}],
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
        parameters=[{'use_sim_time': True}],
        condition=UnlessCondition(dlio),
    )

    # DLIO mode: same bridge, but skip odometry/TF/registered_scan
    # (DLIO provides those when launched separately).
    a2_bridge_dlio = Node(
        package='a2_unitree_bridge',
        executable='a2_bridge_sim',
        output='screen',
        parameters=[{'use_sim_time': True, 'publish_odom': False}],
        condition=IfCondition(dlio),
    )

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'dev': '/dev/input/js0',
            'deadzone': 0.05,
            'autorepeat_rate': 50.0,
            'use_sim_time': True,
        }]
    )

    teleop_node = Node(
        package='a2_ros',
        executable='teleop_joy',
        output='screen',
        parameters=[{
            'linear_x_limit':  0.5,
            'linear_y_limit':  0.5,
            'angular_z_limit': 1.0,
            'use_sim_time': True,
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
    
    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        name='twist_mux',
        output='screen',
            remappings={('/cmd_vel_out', '/cmd_vel')},
        parameters=[
            os.path.join(a2_ros_dir, 'config', 'twist_mux_config.yaml'),
            {'use_sim_time': True},
        ]
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
        headless_arg,
        mujoco_node,
        locomotion_node,
        a2_bridge_node,
        a2_bridge_dlio,
        joy_node,
        twist_mux_node,
        teleop_node,
        robot_state_pub_node,
        rviz_node,
    ])
