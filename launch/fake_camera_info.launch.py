#!/usr/bin/env python3

"""
Launch the synthetic CameraInfo generator and image synchronizer.

This launch file starts the image_to_3d fake_camera_info_node, which subscribes
to a camera image stream and republishes the image together with a synchronized
CameraInfo message.

Launch arguments:
    camera_fov:
        Horizontal and vertical camera field of view in degrees, specified as "HFOV,VFOV".

    input_topic:
        Input camera image topic.

    output_topic:
        Republished image topic synchronized with CameraInfo.

    camera_info_topic:
        Output CameraInfo topic.

    input_type:
        Input image message type: "raw" or "compressed".

    output_type:
        Output image message type: "raw" or "compressed".

    frame_id:
        Optional frame ID override. If empty, the input image frame ID is used.

Launch it:
    ros2 launch image_to_3d fake_camera_info.launch.py
      or
    ros2 launch image_to_3d fake_camera_info.launch.py camera_fov:=92.0,76.0 \
        input_topic:=camera/image_raw/compressed \
        input_type:=compressed \
        output_topic:=camera_3d/image_raw \
        output_type:=raw \
        camera_info_topic:=camera_3d/camera_info \
        frame_id:=fake_camera_link

View the published image and CameraInfo topics:
    ros2 topic echo /camera_3d/camera_info        
    ros2 run image_view image_view --ros-args -r image:=/camera_3d/image_raw -p image_transport:=raw

"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    arguments = [
        DeclareLaunchArgument(
            # for Arducam wide-angle 160 degrees FOV camera module (3280x2464 10-bit RGGB sensor, default 800x600 stream:
            'camera_fov', default_value='92.0,76.0',    # 92.0,69.1 - if keeping 4:3 frame aspect ratio?

            # for Arducam 105 degrees FOV camera module (3280x2464 10-bit RGGB sensor, default 800x600 stream:
            #'camera_fov', default_value='66.0,49.58',   # that's true 4:3 frame aspect ratio

            description='Camera FOV in degrees as HFOV,VFOV'),

        DeclareLaunchArgument(
            'input_topic', default_value='camera/image_raw/compressed'),
        DeclareLaunchArgument(
            'input_type', default_value='compressed',
            description='Input message type: raw or compressed'),

        DeclareLaunchArgument(
            'output_topic', default_value='camera_3d/image_raw'),
        DeclareLaunchArgument(
            'output_type', default_value='raw',
            description='Output message type: raw or compressed'),

        DeclareLaunchArgument(
            'camera_info_topic', default_value='camera_3d/camera_info'),
        DeclareLaunchArgument('frame_id', default_value='camera_3d_link_optical'),
    ]

    node = Node(
        package='image_to_3d',
        executable='fake_camera_info_node',
        name='fake_camera_info_node',
        output='screen',
        parameters=[{
            name: LaunchConfiguration(name)
            for name in (
                'camera_fov', 'input_topic', 'output_topic',
                'camera_info_topic', 'input_type', 'output_type', 'frame_id')
        }],
    )

    return LaunchDescription(arguments + [node])