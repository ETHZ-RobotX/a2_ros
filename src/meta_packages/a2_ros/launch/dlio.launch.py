"""
DLIO (Direct LiDAR-Inertial Odometry) launch for A2 simulation.

Runs DLIO in parallel with the sim — odometry output is NOT wired into the
navigation stack yet, this is for evaluation only.

Topics consumed from the sim:
  /mujoco/front_lidar  (sensor_msgs/PointCloud2) — raw LiDAR from MuJoCo
  /imu/data            (sensor_msgs/Imu)          — published by a2_bridge

Topics published by DLIO:
  /dlio/odom_node/odom   (nav_msgs/Odometry)
  /dlio/odom_node/pose   (geometry_msgs/PoseStamped)
  /dlio/odom_node/path_odom
  /dlio/odom_node/pointcloud/deskewed
  /dlio/map_node/map     (sensor_msgs/PointCloud2)

Usage (run after sim.launch.py is already up):
  ros2 launch a2_ros dlio.launch.py

Or bring it up together with the sim:
  ros2 launch a2_ros sim.launch.py
  ros2 launch a2_ros dlio.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    dlio_pkg = FindPackageShare('direct_lidar_inertial_odometry')
    a2_ros_pkg = get_package_share_directory('a2_ros')

    rviz_arg = DeclareLaunchArgument('rviz', default_value='false', description='Launch RViz with DLIO config')

    dlio_yaml       = PathJoinSubstitution([dlio_pkg, 'cfg', 'dlio.yaml'])
    dlio_params     = PathJoinSubstitution([dlio_pkg, 'cfg', 'params.yaml'])
    a2_params       = os.path.join(a2_ros_pkg, 'config', 'dlio', 'params_a2.yaml')

    dlio_odom_node = Node(
        package='direct_lidar_inertial_odometry',
        executable='dlio_odom_node',
        output='screen',
        parameters=[
            dlio_yaml,
            dlio_params,
            a2_params,
            {'use_sim_time': True},
            # Rename the odom frame to 'map' so the navigation stack (terrain_analysis,
            # local_planner, far_planner) receives /state_estimation in the expected frame.
            {'frames/odom': 'map'},
        ],
        remappings=[
            ('pointcloud', '/mujoco/front_lidar'),
            ('imu',        '/imu/data'),
            ('odom',       '/state_estimation'),
            ('map_pose',                        'dlio/odom_node/map_pose'),
            ('map_pose_inverted',               'dlio/odom_node/map_pose_inverted'),
            ('odom',                            'dlio/odom_node/odom'),
            ('pose',                            'dlio/odom_node/pose'),
            ('path_map',                        'dlio/odom_node/path_map'),
            ('path_odom',                       'dlio/odom_node/path_odom'),
            ('path_map_prop',                   'dlio/odom_node/path_map_prop'),
            ('kf_pose',                         'dlio/odom_node/keyframes'),
            ('kf_cloud',                        'dlio/odom_node/pointcloud/keyframe'),
            ('deskewed',                        'dlio/odom_node/pointcloud/deskewed'),
            ('deskewed_not_transformed',        'dlio/odom_node/pointcloud/deskewed_not_transformed'),
            ('deskewed_and_transformed_to_map', 'dlio/odom_node/pointcloud/deskewed_and_transformed_to_map'),
            ('markers/velocity_linear',         'dlio/odom_node/markers/velocity_linear'),
            ('markers/velocity_angular',        'dlio/odom_node/markers/velocity_angular'),
            ('markers/correction',              'dlio/odom_node/markers/correction'),
            ('markers/degeneracy_directions',   'dlio/odom_node/markers/degeneracy_directions'),
        ],
        respawn=True,
    )

    dlio_map_node = Node(
        package='direct_lidar_inertial_odometry',
        executable='dlio_map_node',
        output='screen',
        parameters=[
            dlio_yaml,
            dlio_params,
            a2_params,
            {'use_sim_time': True},
        ],
        remappings=[
            ('kf_cloud', 'dlio/odom_node/pointcloud/keyframe'),
            ('map_pose', 'dlio/odom_node/map_pose'),
        ],
        respawn=True,
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='dlio_rviz',
        arguments=['-d', PathJoinSubstitution([dlio_pkg, 'launch', 'dlio.rviz'])],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    return LaunchDescription([
        rviz_arg,
        dlio_odom_node,
        dlio_map_node,
        rviz_node,
    ])
