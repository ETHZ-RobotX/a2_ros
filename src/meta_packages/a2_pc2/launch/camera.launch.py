from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Resize resolution — match your detection model's input to minimise bandwidth.
# At 640×640, JPEG q=60 is ~5–8 Mbps at 20 Hz (vs ~200+ Mbps raw).
_WIDTH = 640
_HEIGHT = 640
_JPEG_QUALITY = 60  # 50–70 works well for YOLO; lower = smaller frames
_FRAME_RATE = 5


def generate_launch_description():

    camera_info_url = (
        'package://a2_description/config/camera_info.yaml'
    )

    gscam_config = (
        "udpsrc address=230.1.1.1 port=1720 multicast-iface=eth0 "
        "! queue "
        "! application/x-rtp, media=video, encoding-name=H264 "
        "! rtph264depay ! h264parse ! avdec_h264 "
        "! videoconvert "
        f"! videorate ! video/x-raw,framerate={_FRAME_RATE}/1 "
        f"! videoscale ! video/x-raw,format=I420,width={_WIDTH},height={_HEIGHT} "
        f"! jpegenc quality={_JPEG_QUALITY} "
        "! image/jpeg"
    )

    return LaunchDescription([

        DeclareLaunchArgument(
            'camera_name',
            default_value='camera',
            description='Camera namespace',
        ),
        DeclareLaunchArgument(
            'image_encoding',
            default_value='jpeg',
            description='Image encoding passed to gscam2 — jpeg publishes CompressedImage on image_raw/compressed',
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
                'image_encoding':  LaunchConfiguration('image_encoding'),
                'camera_info_url': LaunchConfiguration('camera_info_url'),
            }],
            remappings=[
                ('image_raw/compressed', 'camera/image/compressed'),
                ('camera_info', 'camera/camera_info'),
            ],
        ),

    ])