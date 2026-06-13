"""
Navigation stack launch for A2 simulation.

Starts the CMU Autonomous Exploration stack on top of the running sim:
  - terrain_analysis     : builds /terrain_map from /registered_scan + /state_estimation
  - terrain_analysis_ext : builds /terrain_map_ext (global terrain for far_planner)
  - local_planner        : obstacle-aware path selection + path follower
  - far_planner          : global visibility-graph planner
  - nav_vel_relay        : converts /nav_vel_cmd (TwistStamped) -> /cmd_vel (Twist)

Prerequisites (provided by sim.launch.py + a2_bridge):
  /state_estimation  - ground-truth odometry (published by a2_bridge in a2_sim_utils)
  /registered_scan   - world-frame lidar cloud (published by a2_bridge in a2_sim_utils)
  /clock             - sim time clock (published by sim_clock in a2_sim_utils)

Usage:
  # Terminal 1
  ros2 launch a2_ros sim.launch.py

  # Terminal 2 (after sim is up)
  ros2 launch a2_ros navigation.launch.py

  # Then set the robot to stand (2) then locomotion (3):
  ros2 topic pub /mode std_msgs/msg/Int32 "data: 2"   # stand up
  ros2 topic pub /mode std_msgs/msg/Int32 "data: 3"   # locomotion

  # Send a navigation goal in RViz using the 'Goalpoint' button,
  # or publish directly:
  ros2 topic pub /way_point geometry_msgs/msg/PointStamped \
    "{header: {frame_id: 'odom'}, point: {x: 5.0, y: 0.0, z: 0.0}}"
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter


def generate_launch_description():
    description_dir = get_package_share_directory('a2_description')
    a2_ros_dir      = get_package_share_directory('a2_ros')
    rviz_path       = os.path.join(description_dir, 'rviz', 'navigation.rviz')
    far_config      = os.path.join(a2_ros_dir, 'config', 'autonomy', 'far_a2.yaml')

    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='false',
        description='Launch RViz2 with navigation config'
    )

    nodes = [
        rviz_arg,
        # Use sim time for all navigation nodes
        SetParameter(name='use_sim_time', value=False),

        # ---- terrain analysis (local map) ----
        Node(
            package='terrain_analysis',
            executable='terrainAnalysis',
            name='terrainAnalysis',
            output='screen',
            parameters=[{
                'scanVoxelSize':       0.05,
                'decayTime':           5.0,
                'noDecayDis':          0.0,
                'clearingDis':         8.0,
                'useSorting':          True,
                'quantileZ':           0.25,
                'considerDrop':        True,
                'limitGroundLift':     True,
                'maxGroundLift':       0.25,
                'vehicleHeight':       0.5,   # A2 is ~0.5 m tall
                'minRelZ':             -1.0,
                'maxRelZ':             1.0,
            }],
        ),

        # ---- terrain analysis ext (global map for far_planner) ----
        Node(
            package='terrain_analysis_ext',
            executable='terrainAnalysisExt',
            name='terrainAnalysisExt',
            output='screen',
            parameters=[{
                'scanVoxelSize':    0.1,
                'decayTime':        2.0,
                'clearingDis':      30.0,
                'useSorting':       True,
                'quantileZ':        0.25,
                'vehicleHeight':    0.5,
                'lowerBoundZ':      -1.0,
                'upperBoundZ':      1.0,
            }],
        ),

        # ---- local planner (obstacle avoidance + path following) ----
        Node(
            package='local_planner',
            executable='localPlanner',
            name='localPlanner',
            output='screen',
            parameters=[{
                'pathFolder':          get_package_share_directory('local_planner') + '/paths',
                'vehicleLength':       0.65,   # A2 body length ~0.65 m
                'vehicleWidth':        0.40,   # A2 body width ~0.40 m
                'twoWayDrive':         False,
                'laserVoxelSize':      0.05,
                'terrainVoxelSize':    0.2,
                'useTerrainAnalysis':  True,
                'checkObstacle':       True,
                'checkRotObstacle':    True,
                'adjacentRange':       3.5,
                'obstacleHeightThre':  0.15,
                'groundHeightThre':    0.1,
                'maxSpeed':            0.5,
                'autonomyMode':        True,
                'autonomySpeed':       0.4,
                'goalClearRange':      0.4,
            }],
        ),

        Node(
            package='local_planner',
            executable='pathFollower',
            name='pathFollower',
            output='screen',
            parameters=[{
                'twoWayDrive':     False,
                'lookAheadDis':    0.4,
                'yawRateGain':     10.0,
                'stopYawRateGain': 8.0,
                'maxYawRate':      45.0,
                'maxSpeed':        0.5,
                'maxAccel':        0.5,
                'stopDisThre':     0.3,
                'slowDwnDisThre':  0.6,
                'autonomyMode':    True,
                'autonomySpeed':   0.4,
            }],
        ),

        # ---- far_planner (global visibility-graph planner) ----
        Node(
            package='far_planner',
            executable='far_planner',
            name='far_planner',
            output='screen',
            # Run headless: no X display in container/SSH, so force Qt offscreen
            # to avoid the xcb plugin aborting (SIGABRT). Planning still works;
            # use RViz instead of the FAR Planner GUI for visualization.
            additional_env={'QT_QPA_PLATFORM': 'offscreen'},
            parameters=[far_config],
            remappings=[
                ('/odom_world',         '/state_estimation'),
                ('/terrain_cloud',      '/terrain_map_ext'),
                ('/scan_cloud',         '/registered_scan'),
                ('/terrain_local_cloud','/terrain_map'),
            ],
        ),

        # ---- relay: /nav_vel_cmd (TwistStamped) -> /cmd_vel (Twist) ----
        Node(
            package='a2_ros',
            executable='nav_vel_relay',
            name='nav_vel_relay',
            output='screen',
        ),

        # ---- sport mode velocity relay: /cmd_vel -> /api/sport/request ----
        # Node(
        #     package='a2_utils',
        #     executable='cmd_vel_sport_relay',
        #     name='cmd_vel_sport_relay',
        #     output='screen',
        # ),
        
        # Node(
        #     package='a2_utils',
        #     executable='registered_scan_pub',
        #     output='screen',
        #     parameters=[{
        #         'use_sim_time': False,
        #         'input_topic':  '/front_lidar/points',
        #         'target_frame': 'map',
        #         'tf_lag_sec':   0.1,
        #     }],
        # ),

        # ---- RViz with navigation config ----
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_path],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ]

    return LaunchDescription(nodes)


def _pkg_exists(pkg):
    try:
        get_package_share_directory(pkg)
        return True
    except Exception:
        return False
