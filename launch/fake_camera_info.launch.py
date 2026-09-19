#!/usr/bin/env python3

"""Launch the fake CameraInfo generator/synchronizer."""

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
            'input_topic', default_value='huskylens/image/compressed'),
        DeclareLaunchArgument(
            'output_topic', default_value='fake_camera/image'),
        DeclareLaunchArgument(
            'camera_info_topic', default_value='fake_camera/camera_info'),
        DeclareLaunchArgument(
            'input_type', default_value='compressed',
            description='Input message type: raw or compressed'),
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
                'camera_info_topic', 'input_type', 'frame_id')
        }],
    )

    return LaunchDescription(arguments + [node])