"""
DLIO (Direct LiDAR-Inertial Odometry) launch — simulation and real robot.

Topics consumed:
  sim:  /mujoco/front_lidar  (PointCloud2)   /imu/data  (published by a2_bridge)
  real: /front_lidar/points  (PointCloud2)   /imu/data  (published by imu_pub in real.launch.py)

Topics published by DLIO:
  /state_estimation  (nav_msgs/Odometry)  — wired into navigation stack
  /dlio/odom_node/*  — raw DLIO outputs

Usage:
  ros2 launch a2_ros dlio.launch.py           # simulation (default)
  ros2 launch a2_ros dlio.launch.py sim:=false  # real robot
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


_DLIO_REMAPS_COMMON = [
    ('odom',                                        '/state_estimation'),
    ('map_pose',                                    'dlio/odom_node/map_pose'),
    ('map_pose_inverted',                           'dlio/odom_node/map_pose_inverted'),
    ('pose',                                        'dlio/odom_node/pose'),
    ('path_map',                                    'dlio/odom_node/path_map'),
    ('path_odom',                                   'dlio/odom_node/path_odom'),
    ('path_map_prop',                               'dlio/odom_node/path_map_prop'),
    ('kf_pose',                                     'dlio/odom_node/keyframes'),
    ('kf_cloud',                                    'dlio/odom_node/pointcloud/keyframe'),
    ('deskewed',                                    'dlio/odom_node/pointcloud/deskewed'),
    ('deskewed_not_transformed',                    'dlio/odom_node/pointcloud/deskewed_not_transformed'),
    ('deskewed_and_transformed_to_map',             '/registered_scan'),
    ('markers/velocity_linear',                     'dlio/odom_node/markers/velocity_linear'),
    ('markers/velocity_angular',                    'dlio/odom_node/markers/velocity_angular'),
    ('markers/correction',                          'dlio/odom_node/markers/correction'),
    ('markers/degeneracy_directions',               'dlio/odom_node/markers/degeneracy_directions'),
]


def generate_launch_description():
    dlio_pkg   = FindPackageShare('direct_lidar_inertial_odometry')
    a2_ros_dir = get_package_share_directory('a2_ros')
    hesai_dir  = get_package_share_directory('hesai_ros_driver')

    sim_arg = DeclareLaunchArgument(
        'sim',
        default_value='true',
        description='true: simulation (MuJoCo lidar + sim time). false: real robot (Hesai lidar + wall time).'
    )
    rviz_arg = DeclareLaunchArgument('rviz', default_value='false', description='Launch RViz with DLIO config')
    output_dir_arg = DeclareLaunchArgument(
        'output_dir',
        default_value='/tmp/a2_dlio_run',
        description='Directory for run_stats output and /save_pcd. Defaults under /tmp.'
    )

    sim        = LaunchConfiguration('sim')
    output_dir = LaunchConfiguration('output_dir')

    dlio_yaml   = PathJoinSubstitution([dlio_pkg, 'cfg', 'dlio.yaml'])
    dlio_params = PathJoinSubstitution([dlio_pkg, 'cfg', 'params.yaml'])
    a2_params   = os.path.join(a2_ros_dir, 'config', 'dlio', 'params_a2.yaml')

    _dlio_base_params = [
        dlio_yaml,
        dlio_params,
        a2_params,
        {'frames/odom': 'map'},
    ]

    # --- sim mode ---
    dlio_odom_sim = Node(
        package='direct_lidar_inertial_odometry',
        executable='dlio_odom_node',
        output='screen',
        parameters=[*_dlio_base_params, {'use_sim_time': True}],
        remappings=[
            ('pointcloud', '/mujoco/front_lidar'),
            ('imu',        '/imu/data'),
            *_DLIO_REMAPS_COMMON,
        ],
        respawn=True,
        condition=IfCondition(sim),
    )

    dlio_map_sim = Node(
        package='direct_lidar_inertial_odometry',
        executable='dlio_map_node',
        output='screen',
        parameters=[*_dlio_base_params, {'use_sim_time': True}],
        remappings=[
            ('kf_cloud', 'dlio/odom_node/pointcloud/keyframe'),
            ('map_pose', 'dlio/odom_node/map_pose'),
        ],
        respawn=True,
        condition=IfCondition(sim),
    )

    # --- real robot mode ---
    hesai_node = Node(
        namespace='hesai_ros_driver',
        package='hesai_ros_driver',
        executable='hesai_ros_driver_node',
        output='screen',
        parameters=[{'config_path': os.path.join(hesai_dir, 'config', 'config_front.yaml')}],
        condition=UnlessCondition(sim),
    )

    dlio_odom_real = Node(
        package='direct_lidar_inertial_odometry',
        executable='dlio_odom_node',
        output='screen',
        parameters=[
            *_dlio_base_params,
            {
                'use_sim_time': False,
                'dynamic_filter/enabled': False,
                'dynamic_filter/max_range': 10.0,
                'dynamic_filter/warmup_scans': 10,
                'dynamic_filter/static_window_scans': 8,
                'dynamic_filter/force_removed_cloud_output': True,
                'dynamic_filter/m_detector/min_history_votes': 4,
                'dynamic_filter/m_detector/case_depth_margin': 0.25,
                'dynamic_filter/m_detector/map_consistency_depth': 0.40,
                'dynamic_filter/m_detector/min_cluster_points': 120,
                'dynamic_filter/m_detector/min_track_cluster_points': 240,
                'dynamic_filter/m_detector/max_cluster_extent': 2.2,
                'dynamic_filter/m_detector/max_assoc_distance': 0.6,
                'dynamic_filter/m_detector/track_confirm_hits': 3,
                'dynamic_filter/m_detector/track_ttl_scans': 8,
                'dynamic_filter/m_detector/static_veto_ratio': 0.10,
                'map/crop/enabled': False,
                'run_stats/enabled': True,
                'run_stats/output_dir': output_dir,
                'run_stats/overwrite': True,
                'run_stats/plot_on_shutdown': True,
                'run_stats/plot_dpi': 600,
            },
        ],
        remappings=[
            ('pointcloud', '/front_lidar/points'),
            ('imu',        '/front_lidar/imu'),
            ('dynamic_removed', 'dlio/odom_node/pointcloud/dynamic_removed'),
            *_DLIO_REMAPS_COMMON,
        ],
        respawn=True,
        condition=UnlessCondition(sim),
    )

    dlio_map_real = Node(
        package='direct_lidar_inertial_odometry',
        executable='dlio_map_node',
        output='screen',
        parameters=[
            *_dlio_base_params,
            {
                'use_sim_time': False,
                'map/crop/enabled': False,
                'map/save_dynamic_removed/enabled': True,
            },
        ],
        remappings=[
            ('kf_cloud',        'dlio/odom_node/pointcloud/keyframe'),
            ('map_pose',        'dlio/odom_node/map_pose'),
            ('map',             'dlio/map_node/map'),
            ('dynamic_removed', 'dlio/odom_node/pointcloud/dynamic_removed'),
        ],
        respawn=True,
        condition=UnlessCondition(sim),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='dlio_rviz',
        arguments=['-d', PathJoinSubstitution([dlio_pkg, 'launch', 'a2_front.rviz'])],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    return LaunchDescription([
        sim_arg,
        rviz_arg,
        output_dir_arg,
        dlio_odom_sim,
        dlio_map_sim,
        # hesai_node,
        dlio_odom_real,
        # dlio_map_real,
        rviz_node,
    ])
