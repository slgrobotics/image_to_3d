#!/usr/bin/env python3

"""
Launch the perception adapter for 3D YOLO detections.

For text-to-speech (pronounce detections):
    sudo apt install flite

Launch it:
    ros2 launch image_to_3d perception_adapter_node.launch.py

"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    person_detected_sound_arg = DeclareLaunchArgument(
        'person_detected_sound',
        default_value='',
        description='Audio file to play when a face is first detected',
    )
    person_detected_text_arg = DeclareLaunchArgument(
        'person_detected_text',
        default_value='person detected',
        description='Text to speak when a face is first detected',
    )
    min_confidence_arg = DeclareLaunchArgument(
        'min_confidence',
        default_value='0.6',
        description='Minimum detection confidence to process',
    )
    face_cooldown_sec_arg = DeclareLaunchArgument(
        'face_cooldown_sec',
        default_value='3.0',
        description='Seconds without a face before resetting tracking state',
    )
    ticker_interval_sec_arg = DeclareLaunchArgument(
        'ticker_interval_sec',
        default_value='0.1',
        description='State-management timer interval in seconds',
    )

    perception_adapter = Node(
        package='image_to_3d',
        executable='perception_adapter_node',
        name='perception_adapter_node',
        output='screen',
        parameters=[{
            'person_detected_sound': LaunchConfiguration('person_detected_sound'),
            'person_detected_text': LaunchConfiguration('person_detected_text'),
            'min_confidence': LaunchConfiguration('min_confidence'),
            'face_cooldown_sec': LaunchConfiguration('face_cooldown_sec'),
            'ticker_interval_sec': LaunchConfiguration('ticker_interval_sec'),
        }],
    )

    return LaunchDescription([
        person_detected_sound_arg,
        person_detected_text_arg,
        min_confidence_arg,
        face_cooldown_sec_arg,
        ticker_interval_sec_arg,
        perception_adapter,
    ])
