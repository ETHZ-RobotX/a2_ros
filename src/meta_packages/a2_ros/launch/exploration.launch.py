"""
Autonomous exploration launch for A2 simulation using TARE planner.

Starts the full exploration stack on top of the running sim:
  - terrain_analysis     : builds /terrain_map from /registered_scan + /state_estimation
  - terrain_analysis_ext : builds /terrain_map_ext (global terrain)
  - local_planner        : obstacle-aware path selection
  - pathFollower         : converts waypoints to velocity, /nav_vel (twist_mux input)
  - tare_planner         : autonomous coverage exploration (replaces far_planner)

Prerequisites (provided by sim.launch.py + a2_bridge):
  /state_estimation  - ground-truth odometry (published by a2_bridge in a2_sim_utils)
  /registered_scan   - world-frame lidar cloud (published by a2_bridge in a2_sim_utils)
  /clock             - sim time clock (published by sim_clock in a2_sim_utils)

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
    rviz_path        = os.path.join(a2_ros_dir, 'rviz', 'exploration.rviz')
    tare_config      = os.path.join(a2_ros_dir, 'config', 'autonomy', 'tare_a2.yaml')

    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Launch RViz2'
    )

    nodes = [
        rviz_arg,
        SetParameter(name='use_sim_time', value=False),

        # ---- terrain analysis (local map) ----
        Node(
            package='terrain_analysis',
            executable='terrainAnalysis',
            name='terrainAnalysis',
            output='screen',
            parameters=[{
                'scanVoxelSize':       0.05,
                'decayTime':           10.0,
                'noDecayDis':          0.0,
                'clearingDis':         8.0,
                'useSorting':          True,
                'quantileZ':           0.25,
                'considerDrop':        True,
                'limitGroundLift':     True,
                'maxGroundLift':       0.25,
                'clearDyObs':          False,
                'minDyObsDis':         0.3,
                'minDyObsAngle':       0.0,
                'minDyObsRelZ':        -0.5,
                'absDyObsRelZThre':    0.2,
                'minDyObsVFOV':        -16.0,
                'maxDyObsVFOV':        16.0,
                'minDyObsPointNum':    1,
                'noDataObstacle':      False,
                'noDataBlockSkipNum':  0,
                'minBlockPointNum':    10,
                'vehicleHeight':       0.5,
                'voxelPointUpdateThre': 100,
                'voxelTimeUpdateThre': 2.0,
                'minRelZ':             -1.0,
                'maxRelZ':             1.0,
                'disRatioZ':           0.2,
            }],
        ),

        # ---- terrain analysis ext (global map) ----
        Node(
            package='terrain_analysis_ext',
            executable='terrainAnalysisExt',
            name='terrainAnalysisExt',
            output='screen',
            parameters=[{
                'scanVoxelSize':        0.1,
                'decayTime':            10.0,
                'noDecayDis':           0.0,
                'clearingDis':          30.0,
                'useSorting':           True,
                'quantileZ':            0.25,
                'vehicleHeight':        0.5,
                'voxelPointUpdateThre': 100,
                'voxelTimeUpdateThre':  2.0,
                'lowerBoundZ':          -1.0,
                'upperBoundZ':          1.0,
                'disRatioZ':            0.1,
                'checkTerrainConn':     True,
                'terrainUnderVehicle':  -0.75,
                'terrainConnThre':      0.5,
                'ceilingFilteringThre': 2.0,
                'localTerrainMapRadius': 4.0,
            }],
        ),
        # ---- local planner ----
        Node(
            package='local_planner',
            executable='localPlanner',
            name='localPlanner',
            output='screen',
            parameters=[{
                'pathFolder':          get_package_share_directory('local_planner') + '/paths',
                'vehicleLength':       0.65,
                'vehicleWidth':        0.40,
                'sensorOffsetX':       0.0,
                'sensorOffsetY':       0.0,
                'twoWayDrive':         False,
                'laserVoxelSize':      0.05,
                'terrainVoxelSize':    0.2,
                'useTerrainAnalysis':  True,
                'checkObstacle':       True,
                'checkRotObstacle':    True,
                'adjacentRange':       3.5,
                'obstacleHeightThre':  0.25,
                'groundHeightThre':    0.1,
                'costHeightThre':      0.1,
                'costScore':           0.02,
                'useCost':             False,
                'pointPerPathThre':    2,
                'minRelZ':             -0.5,
                'maxRelZ':             0.8,
                'maxSpeed':            0.5,
                'dirWeight':           0.1,
                'dirThre':             90.0,
                'dirToVehicle':        False,
                'pathScale':           1.0,
                'minPathScale':        0.75,
                'pathScaleStep':       0.25,
                'pathScaleBySpeed':    True,
                'minPathRange':        1.0,
                'pathRangeStep':       0.5,
                'pathRangeBySpeed':    True,
                'pathCropByGoal':      True,
                'autonomyMode':        True,
                'autonomySpeed':       2.0,
                'joyToSpeedDelay':     2.0,
                'joyToCheckObstacleDelay': 5.0,
                'goalClearRange':      0.4,
                'goalX':               0.0,
                'goalY':               0.0,
            }],
        ),

        Node(
            package='local_planner',
            executable='pathFollower',
            name='pathFollower',
            output='screen',
            parameters=[{
                'sensorOffsetX':    0.0,
                'sensorOffsetY':    0.0,
                'pubSkipNum':       1,
                'twoWayDrive':      False,
                'lookAheadDis':     0.4,
                'yawRateGain':      10.0,
                'stopYawRateGain':  8.0,
                'maxYawRate':       45.0,
                'maxSpeed':         0.5,
                'maxAccel':         2.0,
                'switchTimeThre':   1.0,
                'dirDiffThre':      0.1,
                'stopDisThre':      0.3,
                'slowDwnDisThre':   0.6,
                'useInclRateToSlow': False,
                'inclRateThre':     120.0,
                'slowRate1':        0.25,
                'slowRate2':        0.5,
                'slowTime1':        2.0,
                'slowTime2':        2.0,
                'useInclToStop':    False,
                'inclThre':         45.0,
                'stopTime':         5.0,
                'noRotAtStop':      False,
                'noRotAtGoal':      True,
                'autonomyMode':     True,
                'autonomySpeed':    2.0,
                'joyToSpeedDelay':  2.0,
            }],
        ),

        # ---- TARE planner (autonomous exploration) ----
        Node(
            package='tare_planner',
            executable='tare_planner_node',
            name='tare_planner_node',
            output='screen',
            parameters=[tare_config],
        ),


        # ---- RViz ----
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_path],
            parameters=[{'use_sim_time': False}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ]

    return LaunchDescription(nodes)
