#!/usr/bin/env python3

"""
camera_relay.launch.py - helps to avoid duplicate camera traffic over WiFi 

Problem: 
    - a camera on the robot publishes `camera/image_raw/compressed`
    - several clients on a Workstation subscribe to it - for processing and viewing
    - each subscription consumes ~7 MBits/s of the WiFi capacity and quickly overwhelms it

Solution:
    - remap the original topic on the robot to `camera_0/camera/image_raw/compressed`
    - only allow one client ROS node on the Workstation to subscribe to that camera topic
    - that client (relay) should copy the robot's camera messages to `camera/image_raw/compressed`
    - clients on the Workstation (processing, RViz2, etc.) subscribe to the
          relayed topic, avoiding additional robot-to-workstation camera traffic over WiFi

Tip: a typical "run_arducam.sh" Arducam launch file on the robot might look like this:
------------
#!/bin/bash

#
# running Arducam at 5 FPS 800x600
#

set -x

# no remapping:
#ros2 run camera_ros camera_node --ros-args -p FrameDurationLimits:="[200000,200000]"

# Remap all topics via namespace assignment, produces '/camera_0/camera/image_raw/compressed':
ros2 run camera_ros camera_node --ros-args -p FrameDurationLimits:="[200000,200000]" -r __ns:=/camera_0

# or, remap individual topic:
# -r camera/image_raw/compressed:=camera_0/camera/image_raw/compressed

set +x
------------

Launch it on the Workstation:
    ros2 launch image_to_3d camera_relay.launch.py

"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    camera_input_topic_arg = DeclareLaunchArgument(
        'camera_input_topic',
        default_value='/camera_0/camera/image_raw/compressed',   # camera on robot
        description='Camera topic as published on the robot')

    camera_output_topic_arg = DeclareLaunchArgument(
        'camera_output_topic',
        default_value='/camera/image_raw/compressed',   # camera on the Workstation
        description='Camera topic as relayed / published on the Workstation')

    camera_topic_relay = Node(
        package='topic_tools',
        executable='relay',
        name='camera_topic_relay',
        arguments=[
            LaunchConfiguration('camera_input_topic'),
            LaunchConfiguration('camera_output_topic'),
        ],
        output='screen',
    )

    return LaunchDescription([
        camera_input_topic_arg,
        camera_output_topic_arg,
        LogInfo(msg=[
            'Camera topic relay:',
        ]),
        LogInfo(msg=[
            '    camera_input_topic:=',
            LaunchConfiguration('camera_input_topic'),
        ]),
        LogInfo(msg=[
            '    camera_output_topic:=',
            LaunchConfiguration('camera_output_topic'),
        ]),
        camera_topic_relay,
    ])
