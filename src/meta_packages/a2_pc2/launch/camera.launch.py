from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    gscam_config = (
        "udpsrc address=230.1.1.1 port=1720 multicast-iface=eth0 "
        "! queue "
        "! application/x-rtp, media=video, encoding-name=H264 "
        "! rtph264depay ! h264parse ! avdec_h264 "
        "! videoconvert "
        "! video/x-raw,format=RGB"
    )

    return LaunchDescription([

        DeclareLaunchArgument(
            'camera_name',
            default_value='camera',
            description='Camera namespace',
        ),
        DeclareLaunchArgument(
            'image_encoding',
            default_value='rgb8',
            description='Image encoding passed to gscam2',
        ),
        DeclareLaunchArgument(
            'gscam_config',
            default_value=gscam_config,
            description='GStreamer pipeline string',
        ),

        Node(
            package='gscam2',
            executable='gscam_main',
            name='gscam2',
            output='screen',
            parameters=[{
                'gscam_config':    LaunchConfiguration('gscam_config'),
                'camera_name':     LaunchConfiguration('camera_name'),
                'image_encoding':  LaunchConfiguration('image_encoding'),
            }],
            remappings=[
                ('image_raw', 'camera/image_raw'),
            ],
        ),

    ])