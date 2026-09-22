#!/usr/bin/env python3

"""
Launch all the nodes in this package.

Prerequisites:
    - The camera must be publishing images and camera info to the topics:
        - /camera/color/image_raw
        - /camera/color/camera_info

    - Depth Anything V2 HTTP Server must be running and accepting requests:
        - URL: http://localhost:5001/depth 


Launch it:
    ros2 launch image_to_3d all.launch.py

"""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    launch_directory = get_package_share_directory('image_to_3d') + '/launch'
    launch_files = [
        'fake_camera_info.launch.py',
        'image_to_depth_node.launch.py',
        'depth_to_laserscan.launch.py',
        'launch_rviz.launch.py',
        #'point_cloud_node.launch.py',
        'point_cloud_rgb_node.launch.py',
    ]

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                launch_directory + '/' + launch_file
            )
        )
        for launch_file in launch_files
    ])