#!/usr/bin/env python3

"""
point_cloud_node.launch.py -
    launch the depth -> point cloud conversion node
    (from a standard ROS2 depth_image_proc package)

Install prerequisites:

    sudo apt install ros-${ROS_DISTRO}-image-pipeline

Launch it:

    ros2 launch image_to_3d point_cloud_node.launch.py

"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='depth_image_proc',
            executable='point_cloud_xyz_node',
            name='depth_point_cloud',
            output='screen',
            remappings=[
                ('camera_info', 'camera_3d/depth/camera_info'),  # must be synchronized with depth image below
                ('image_rect', 'camera_3d/depth/image_16UC1'),
                ('points', 'camera_3d/depth/points'),
            ],
        ),
    ])
