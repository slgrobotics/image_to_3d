#!/usr/bin/env python3

"""
image_to_depth_node.launch.py - launch the node querying the Depth Anything V2 server for depth maps/images

Works with the HuskyLens 2 MCP node (launch/huskylens2_mcp.launch.py), or any other node publishing compressed images.

Make sure that the Depth Anything V2 server is running, e.g.:
  cd ~/husky_ws/src/image_to_3d/depth_anything
  ... activate your Python 3 virtual environment ...
  ./depth_server.py

Launch it:
  ros2 launch image_to_3d image_to_depth_node.launch.py

  ros2 launch image_to_3d image_to_depth_node.launch.py depth_server:=http://127.0.0.1:5001/depth

"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('image_to_3d')
    default_config  = os.path.join(pkg_dir, 'config', 'huskylens2.yaml')

    # default values here override the YAML file, but can be overridden by launch arguments

    depth_server_arg = DeclareLaunchArgument(
        'depth_server',
        default_value='http://127.0.0.1:5001/depth',
        description='Depth Anything V2 server base URL')

    config_arg = DeclareLaunchArgument(
        'params_file',
        default_value=default_config,
        description='Path to the ROS 2 parameter YAML file.')

    image_to_depth_node = Node(
        package='image_to_3d',
        executable='image_to_depth_node',
        name='image_to_depth_node',
        output='screen',
        parameters=[
            LaunchConfiguration('params_file'),
           {
                'depth_server': LaunchConfiguration('depth_server'),
            },
        ],
    )

    # If this package is launched without corresponding robot's URDF and TF tree,
    #  then we need to publish a static transform from the camera optical frame to the map frame
    #  for RViz2 visualization. The following two static transform publishers are for that purpose.

    # static transform publisher "map->huskylens2_link" for RViz2:
    tf_camera_to_map = Node(package = "tf2_ros", 
                    executable = "static_transform_publisher",
                    arguments=[
                        '--x', '5.0',     # X translation in meters
                        '--y', '0.0',     # Y translation in meters
                        '--z', '0.57',    # Z translation in meters (camera height above ground)
                        '--roll',  '3.14159265359',  # Roll in radians
                        '--pitch', '0.0', # Pitch in radians
                        '--yaw',   '3.14159265359',   # Yaw in radians (e.g., 1.57079632679 = 90 degrees)
                        '--frame-id', 'map', # Parent frame ID
                        '--child-frame-id', 'huskylens2_link' # Child frame ID
                    ]
    )


    # static transform publisher "map->huskylens2_link_optical" for RViz2:
    tf_camera_optical_to_map = Node(package = "tf2_ros", 
                    executable = "static_transform_publisher",
                    arguments=[
                        '--x', '5.0',     # X translation in meters
                        '--y', '0.0',     # Y translation in meters
                        '--z', '0.57',    # Z translation in meters (camera height above ground)
                        '--roll', '-1.57079632679',  # Roll in radians
                        '--pitch', '0.0', # Pitch in radians
                        '--yaw', '1.57079632679',   # Yaw in radians (e.g., 1.57079632679 = 90 degrees)
                        '--frame-id', 'map', # Parent frame ID
                        '--child-frame-id', 'huskylens2_link_optical' # Child frame ID
                    ]
    )


    return LaunchDescription([
        depth_server_arg,
        config_arg,
        tf_camera_to_map,
        tf_camera_optical_to_map,
        image_to_depth_node,
    ])
