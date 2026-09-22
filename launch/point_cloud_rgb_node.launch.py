#!/usr/bin/env python3

"""
point_cloud_rgb_node.launch.py

    Decompress the HuskyLens (or other camera) RGB image and generate an XYZRGB point cloud
    from the RGB image and metric depth image.

Install prerequisites:
    sudo apt install ros-${ROS_DISTRO}-image-pipeline
    sudo apt install ros-${ROS_DISTRO}-image-transport-plugins

Launch it:
    ros2 launch image_to_3d point_cloud_rgb_node.launch.py

"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
        # ------------------------------------------------------------------
        # Decompress camera's RGB image:
        #
        #   /camera/image_raw/compressed
        #       sensor_msgs/msg/CompressedImage
        #
        #              ↓
        #
        #   /camera_3d/image_raw
        #       sensor_msgs/msg/Image
        #
        # image_transport operates on base topic names. The "compressed"
        # input transport therefore subscribes to:
        #
        #   /camera/image_raw/compressed
        #
        # while the "raw" output transport publishes:
        #
        #   /camera_3d/image_raw
        # ------------------------------------------------------------------
        camera_rgb_decompress_node = Node(
            package='image_transport',
            executable='republish',
            name='camera_rgb_decompress',
            output='screen',
            parameters=[{
                'in_transport': 'compressed',
                'out_transport': 'raw',
            }],
            remappings=[
                ('in/compressed', '/camera/image_raw/compressed'),
                ('out', '/camera_3d/image_raw'),
            ],
        )

        # ------------------------------------------------------------------
        # RGB + depth → XYZRGB point cloud
        #
        # RGB:
        #   /camera_3d/image/raw
        #
        # Depth:
        #   /camera_3d/depth/image_16UC1
        #       encoding: 16UC1
        #       units: millimeters
        #
        # Camera calibration:
        #   /camera_3d/depth/camera_info
        #
        # Output:
        #   /camera_3d/depth/points
        #       sensor_msgs/msg/PointCloud2
        # ------------------------------------------------------------------
        point_cloud_xyzrgb_node = Node(
            package='depth_image_proc',
            executable='point_cloud_xyzrgb_node',
            name='depth_point_cloud_xyzrgb',
            output='screen',
            remappings=[
                (
                    'rgb/image_rect_color',
                    'camera_3d/image_raw'
                ),
                (
                    'rgb/camera_info',
                    'camera_3d/depth/camera_info'
                ),
                (
                    'depth_registered/image_rect',
                    'camera_3d/depth/image_16UC1'
                ),
                (
                    'points',
                    'camera_3d/depth/points'
                ),
            ],
        )

        return LaunchDescription([
            #camera_rgb_decompress_node,
            point_cloud_xyzrgb_node,
        ])
