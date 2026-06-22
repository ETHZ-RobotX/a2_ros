from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock (set true when running in sim)'
    )

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'dev': '/dev/input/js0',  # Standard linux joystick path
            'deadzone': 0.05,
            'autorepeat_rate': 50.0,
        }]
    )

    teleop_joy = Node(
        package='a2_ros',
        executable='teleop_joy',
        output='screen',
        parameters=[{
            'linear_x_limit':  0.15,
            'linear_y_limit':  0.10,
            'angular_z_limit': 0.10,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }]
    )

    return LaunchDescription([
        use_sim_time_arg,
        joy_node,
        teleop_joy,
    ])
