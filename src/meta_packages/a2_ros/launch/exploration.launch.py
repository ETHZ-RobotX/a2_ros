"""
Autonomous exploration launch for A2 simulation using TARE planner.

Starts the full exploration stack on top of the running sim:
  - terrain_analysis     : builds /terrain_map from /registered_scan + /state_estimation
  - terrain_analysis_ext : builds /terrain_map_ext (global terrain)
  - local_planner        : obstacle-aware path selection
  - pathFollower         : converts waypoints to /cmd_vel
  - tare_planner         : autonomous coverage exploration (replaces far_planner)
  - nav_vel_relay        : converts /nav_vel_cmd (TwistStamped) -> /cmd_vel (Twist)

Prerequisites (provided by sim.launch.py + a2_bridge):
  /state_estimation  - ground-truth odometry (published by a2_bridge)
  /registered_scan   - world-frame lidar cloud (published by a2_bridge)
  /clock             - sim time clock (published by a2_bridge)

Usage:
  # Terminal 1
  ros2 launch a2_ros sim.launch.py scene:=scene_obstacles.xml

  # Terminal 2
  cd src/control/a2_locomotion_controller/scripts
  ./control_mode.sh --stand
  ./control_mode.sh --walk

  # Terminal 3
  ros2 launch a2_ros exploration.launch.py rviz:=true

The robot will begin exploring autonomously.
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
    rviz_path        = os.path.join(description_dir, 'rviz', 'exploration.rviz')
    tare_config      = os.path.join(a2_ros_dir, 'config', 'autonomy', 'tare_a2.yaml')

    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Launch RViz2'
    )

    nodes = [
        rviz_arg,
        SetParameter(name='use_sim_time', value=True),

        # ---- terrain analysis (local map) ----
        Node(
            package='terrain_analysis',
            executable='terrainAnalysis',
            name='terrainAnalysis',
            output='screen',
            parameters=[{
                'scanVoxelSize':    0.05,
                'decayTime':        5.0,
                'noDecayDis':       0.0,
                'clearingDis':      8.0,
                'useSorting':       True,
                'quantileZ':        0.25,
                'considerDrop':     True,
                'limitGroundLift':  True,
                'maxGroundLift':    0.25,
                'vehicleHeight':    0.5,
                'minRelZ':          -1.0,
                'maxRelZ':          1.0,
            }],
        ),

        # ---- terrain analysis ext (global map) ----
        Node(
            package='terrain_analysis_ext',
            executable='terrainAnalysisExt',
            name='terrainAnalysisExt',
            output='screen',
            parameters=[{
                'scanVoxelSize':  0.1,
                'decayTime':      2.0,
                'clearingDis':    30.0,
                'useSorting':     True,
                'quantileZ':      0.25,
                'vehicleHeight':  0.5,
                'lowerBoundZ':    -1.0,
                'upperBoundZ':    1.0,
            }],
        ),

        # ---- local planner ----
        Node(
            package='local_planner',
            executable='localPlanner',
            name='localPlanner',
            output='screen',
            parameters=[{
                'pathFolder':         get_package_share_directory('local_planner') + '/paths',
                'vehicleLength':      0.65,
                'vehicleWidth':       0.40,
                'twoWayDrive':        False,
                'laserVoxelSize':     0.05,
                'terrainVoxelSize':   0.2,
                'useTerrainAnalysis': True,
                'checkObstacle':      True,
                'checkRotObstacle':   True,
                'adjacentRange':      3.5,
                'obstacleHeightThre': 0.15,
                'groundHeightThre':   0.1,
                'maxSpeed':           0.5,
                'autonomyMode':       True,
                'autonomySpeed':      0.4,
                'goalClearRange':     0.4,
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

        # ---- republish /state_estimation stamped to each scan ----
        Node(
            package='a2_ros',
            executable='scan_pose_sync',
            name='scan_pose_sync',
            output='screen',
        ),

        # ---- TARE planner (autonomous exploration) ----
        Node(
            package='tare_planner',
            executable='tare_planner_node',
            name='tare_planner_node',
            output='screen',
            parameters=[tare_config],
        ),

        # ---- relay: /nav_vel_cmd (TwistStamped) -> /cmd_vel (Twist) ----
        Node(
            package='a2_ros',
            executable='nav_vel_relay',
            name='nav_vel_relay',
            output='screen',
        ),

        # ---- RViz ----
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
