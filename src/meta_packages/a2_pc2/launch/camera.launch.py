from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

_WIDTH = 640
_HEIGHT = 360
_FRAME_RATE = 5
_JPEG_QUALITY = 60


def generate_launch_description():

    camera_info_url = (
        'package://a2_description/config/camera_info_real.yaml'
    )

    gscam_config = (
        "udpsrc address=230.1.1.1 port=1720 multicast-iface=eth0 "
        "! queue "
        "! application/x-rtp, media=video, encoding-name=H264 "
        "! rtph264depay ! h264parse ! avdec_h264 "
        "! videoconvert "
        f"! videorate ! video/x-raw,framerate={_FRAME_RATE}/1 "
        f"! videoscale ! video/x-raw,width={_WIDTH},height={_HEIGHT} "
        "! videoconvert "
    )

    print(f"gscam_config: {gscam_config}")

    return LaunchDescription([

        DeclareLaunchArgument(
            'camera_name',
            default_value='camera',
            description='Camera namespace',
        ),
        DeclareLaunchArgument(
            'gscam_config',
            default_value=gscam_config,
            description='GStreamer pipeline string',
        ),
        DeclareLaunchArgument(
            'camera_info_url',
            default_value=camera_info_url,
            description='URL to camera calibration YAML',
        ),

        Node(
            package='gscam2',
            executable='gscam_main',
            name='gscam2',
            output='screen',
            parameters=[{
                'gscam_config':    LaunchConfiguration('gscam_config'),
                'camera_name':     LaunchConfiguration('camera_name'),
                'image_encoding':  'rgb8',
                'camera_info_url': LaunchConfiguration('camera_info_url'),
                # Must match the camera optical frame in a2.urdf so the
                # lidar->camera TF lookup in object_detection resolves.
                # gscam2 otherwise defaults frame_id to "camera_frame",
                # which is not in the robot's TF tree.
                'frame_id':        'front_camera_optical_frame',
            }],
            remappings=[
                ('image_raw', 'camera/image_raw'),
                ('camera_info', 'camera/camera_info'),
            ],
        ),

        Node(
            package='image_transport',
            executable='republish',
            name='image_republish',
            arguments=['raw', 'compressed'],
            remappings=[
                ('in', 'camera/image_raw'),
                ('out/compressed', 'camera/image_raw/compressed'),
            ],
            parameters=[{
                'jpeg_quality': _JPEG_QUALITY,
            }],
        ),

    ])
