#!/usr/bin/env python3

"""
camera_to_map_tf.launch.py - relates camera and camera optical frame to map frame for RViz2 demo

If this package is launched without corresponding robot's URDF and TF tree,
  then we need to publish a static transform from the camera optical frame to the map frame
  for RViz2 visualization. The following static transform publishers are for that purpose.

See https://github.com/slgrobotics/huskylens2_ros2/blob/main/README.md#the-optical-coordinate-system-for-cameras-and-sensors

Launch it:
    ros2 launch image_to_3d camera_to_map_tf.launch.py

    ros2 launch image_to_3d camera_to_map_tf.launch.py \
        camera_pos_height:=1.0 \
        camera_pos_pitch:=10.0

"""

import os
from math import pi
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('image_to_3d')

    camera_pos_height_arg = DeclareLaunchArgument(
        'camera_pos_height',
        #default_value= '1.0',   # Dragger's "stereo" either of the cameras
        default_value= '0.57',   # Seggy's 160 degrees FOV camera
        description='Camera position over ground plane')

    camera_pos_pitch_arg = DeclareLaunchArgument(
        'camera_pos_pitch',
        #default_value='4.0',   # Dragger's "stereo" either of the cameras
        default_value='0.0',    # Seggy's 160 degrees FOV camera
        description='Compensating camera pitch related to ground plane, degrees, if looking up = positive')

    # static transform publisher "camera_3d_link->map" for RViz2:
    tf_camera_3d_to_map = Node(package = "tf2_ros", 
                    executable = "static_transform_publisher",
                    name="tf_camera_3d_to_map",
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
    tf_camera_3d_optical_to_map = Node(package = "tf2_ros", 
                    executable = "static_transform_publisher",
                    name="tf_camera_3d_optical_to_map",
                    arguments=[
                        '--x', '0.0',       # X translation in meters
                        '--y', '0.0',       # Y translation in meters
                        '--z', '0.0',       # Z translation in meters (camera height above ground)
                        '--roll', str(-pi / 2),  # Roll in radians
                        '--pitch', '0.0',   # Pitch in radians
                        '--yaw', str(pi / 2),   # Yaw in radians (90 degrees)
                        '--frame-id', 'camera_3d_link', # Parent frame ID
                        '--child-frame-id', 'camera_3d_link_optical' # Child frame ID
                    ]
    )

    # static transform publisher "camera_3d_link_laserscan->camera_3d_link" for RViz2:
    tf_camera_3d_laserscan_to_map = Node(package = "tf2_ros", 
                    executable = "static_transform_publisher",
                    name="tf_camera_3d_laserscan_to_map",
                    arguments=[
                        '--x', '0.0',       # X translation in meters
                        '--y', '0.0',       # Y translation in meters
                        '--z', '0.0',       # Z translation in meters (camera height above ground)
                        '--roll', str(pi),  # Roll in radians
                        '--pitch', '0.0',   # Pitch in radians
                        '--yaw', str(pi),   # Yaw in radians (90 degrees)
                        '--frame-id', 'camera_3d_link', # Parent frame ID
                        '--child-frame-id', 'camera_3d_link_laserscan' # Child frame ID
                    ]
    )

    # static transform publisher "camera_3d_link_laserscan->camera_3d_link_optical" for RViz2:
    tf_camera_3d_laserscan_to_optical = Node(package = "tf2_ros", 
                    executable = "static_transform_publisher",
                    name="tf_camera_3d_laserscan_to_optical",
                    arguments=[
                        '--x', '0.0',       # X translation in meters
                        '--y', '0.0',       # Y translation in meters
                        '--z', '0.0',       # Z translation in meters (camera height above ground)
                        '--roll', str(-pi / 2), # Roll in radians
                        '--pitch', str(-pi / 2), # Pitch in radians
                        '--yaw', '0.0',     # Yaw in radians (90 degrees)
                        '--frame-id', 'camera_3d_link_optical', # Parent frame ID
                        '--child-frame-id', 'camera_3d_link_laserscan' # Child frame ID
                    ]
    )


    return LaunchDescription([
        camera_pos_height_arg,
        camera_pos_pitch_arg,
        LogInfo(msg=[
            'Camera position:',
        ]),
        LogInfo(msg=[
            '    camera_pos_height:=',
            LaunchConfiguration('camera_pos_height'),
            ' m',
        ]),
        LogInfo(msg=[
            '    camera_pos_pitch:=',
            LaunchConfiguration('camera_pos_pitch'),
            ' degrees',
        ]),
        tf_camera_3d_to_map,
        tf_camera_3d_optical_to_map,
        #tf_camera_3d_laserscan_to_map,
        tf_camera_3d_laserscan_to_optical,
    ])
