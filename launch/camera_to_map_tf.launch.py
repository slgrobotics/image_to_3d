#!/usr/bin/env python3

"""
camera_to_map_tf.launch.py - relates camera and camera optical frame to map frame for RViz2 demo

Launch it:
    ros2 launch image_to_3d camera_to_map_tf.launch.py

    ros2 launch image_to_3d camera_to_map_tf.launch.py \
        request_timeout:=10.0 \
        request_timeout:=10.0

"""

import os
from math import pi
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('image_to_3d')

    camera_pos_height_arg = DeclareLaunchArgument(
        'camera_pos_height',
        default_value= '1.0',
        description='Camera position over ground plane')

    camera_pos_pitch_arg = DeclareLaunchArgument(
        'camera_pos_pitch',
        default_value='4.0',
        description='Camera pitch related to ground plane, degrees, looking up = positive')


    # If this package is launched without corresponding robot's URDF and TF tree,
    #  then we need to publish a static transform from the camera optical frame to the map frame
    #  for RViz2 visualization. The following two static transform publishers are for that purpose.
    # See https://github.com/slgrobotics/huskylens2_ros2/blob/main/README.md#the-optical-coordinate-system-for-cameras-and-sensors

    # static transform publisher "camera_3d_link->map" for RViz2:
    tf_camera_to_map = Node(package = "tf2_ros", 
                    executable = "static_transform_publisher",
                    arguments=[
                        '--x', '5.0',     # X translation in meters
                        '--y', '0.0',     # Y translation in meters
                        '--z', PythonExpression([
                            'float(', LaunchConfiguration('camera_pos_height'), ')' ]),    # Z translation in meters (camera height above ground)
                        #'--z', '0.57',    # Z translation in meters (camera height above ground)
                        '--roll',  '0.0', # Roll in radians
                        '--pitch', PythonExpression([
                            'float(', LaunchConfiguration('camera_pos_pitch'), ') * 3.141592653589793 / 180.0',
                        ]), # Pitch in radians
                        #'--pitch', '0.0', # Pitch in radians
                        '--yaw',   '0.0', # Yaw in radians (e.g., 1.57079632679 = 90 degrees)
                        '--frame-id', 'map', # Parent frame ID
                        '--child-frame-id', 'camera_3d_link' # Child frame ID
                    ]
    )


    # static transform publisher "camera_3d_link_optical->camera_3d_link" for RViz2:
    tf_camera_optical_to_map = Node(package = "tf2_ros", 
                    executable = "static_transform_publisher",
                    arguments=[
                        '--x', '0.0',     # X translation in meters
                        '--y', '0.0',     # Y translation in meters
                        '--z', '0.0',     # Z translation in meters (camera height above ground)
                        '--roll', str(-pi / 2),  # Roll in radians
                        '--pitch', '0.0', # Pitch in radians
                        '--yaw', str(pi / 2),   # Yaw in radians (90 degrees)
                        '--frame-id', 'camera_3d_link', # Parent frame ID
                        '--child-frame-id', 'camera_3d_link_optical' # Child frame ID
                    ]
    )


    return LaunchDescription([
        camera_pos_height_arg,
        camera_pos_pitch_arg,
        tf_camera_to_map,
        tf_camera_optical_to_map,
    ])
