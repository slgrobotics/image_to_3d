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
        input_topic:=camera/image/compressed \
        output_topic:=camera_3d/image \
        camera_info_topic:=camera_3d/camera_info \
        input_type:=compressed \
        output_type:=raw \
        frame_id:=fake_camera_link
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    arguments = [
        DeclareLaunchArgument(
            'camera_fov', default_value='92.0,76.0',
            description='Camera FOV in degrees as HFOV,VFOV'),
        DeclareLaunchArgument(
            'input_topic', default_value='camera/image/compressed'),
        DeclareLaunchArgument(
            'output_topic', default_value='camera_3d/image'),
        DeclareLaunchArgument(
            'camera_info_topic', default_value='camera_3d/camera_info'),
        DeclareLaunchArgument(
            'input_type', default_value='compressed',
            description='Input message type: raw or compressed'),
        DeclareLaunchArgument(
            'output_type', default_value='raw',
            description='Output message type: raw or compressed'),
        DeclareLaunchArgument('frame_id', default_value=''),
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