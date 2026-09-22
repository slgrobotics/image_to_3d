#!/usr/bin/env python3

"""
Launch RViz2 with the package's configured visualization layout.

Launch it:
    ros2 launch image_to_3d launch_rviz.launch.py

"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
	package_share = get_package_share_directory('image_to_3d')
	rviz_config = os.path.join(package_share, 'config', 'rviz2.rviz')

	return LaunchDescription([
		Node(
			package='rviz2',
			executable='rviz2',
			name='rviz2',
			output='screen',
			arguments=['-d', rviz_config],
		),
	])
