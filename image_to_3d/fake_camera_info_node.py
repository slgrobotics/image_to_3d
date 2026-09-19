#!/usr/bin/env python3
"""Publish synthetic CameraInfo synchronized with an image topic."""

import math

import rclpy
from cv_bridge import CvBridge
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, CompressedImage, Image


def parse_fov(value):
    try:
        horizontal_fov, vertical_fov = (
            float(component.strip()) for component in str(value).split(','))
    except (TypeError, ValueError):
        raise ValueError(
            f'Invalid camera_fov {value!r}; expected "HFOV,VFOV"') from None

    if not (
            math.isfinite(horizontal_fov)
            and math.isfinite(vertical_fov)
            and 0.0 < horizontal_fov < 180.0
            and 0.0 < vertical_fov < 180.0):
        raise ValueError(
            'camera_fov HFOV and VFOV must be between 0 and 180 degrees')
    return horizontal_fov, vertical_fov


class FakeCameraInfoNode(Node):

    def __init__(self):
        super().__init__('fake_camera_info_node')

        self.declare_parameter('camera_fov', '92.0,76.0')
        self.declare_parameter('input_topic', 'huskylens/image/compressed')
        self.declare_parameter('output_topic', 'fake_camera/image')
        self.declare_parameter('camera_info_topic', 'fake_camera/camera_info')
        self.declare_parameter('input_type', 'compressed')
        self.declare_parameter('frame_id', '')

        self._horizontal_fov, self._vertical_fov = parse_fov(
            self.get_parameter('camera_fov').value)
        input_topic = str(self.get_parameter('input_topic').value)
        output_topic = str(self.get_parameter('output_topic').value)
        camera_info_topic = str(
            self.get_parameter('camera_info_topic').value)
        input_type = str(self.get_parameter('input_type').value).strip().lower()
        self._frame_id = str(self.get_parameter('frame_id').value)

        if input_type not in ('raw', 'compressed'):
            raise ValueError('input_type must be either raw or compressed')
        self._compressed = input_type == 'compressed'

        image_type = CompressedImage if self._compressed else Image
        self._image_pub = self.create_publisher(image_type, output_topic, 10)
        self._camera_info_pub = self.create_publisher(
            CameraInfo, camera_info_topic, 10)
        self._bridge = CvBridge()

        self.create_subscription(
            image_type, input_topic, self._on_image, qos_profile_sensor_data)

        self.get_logger().info(
            f'Synchronizing {input_type} images from {input_topic} to '
            f'{output_topic} with CameraInfo on {camera_info_topic}')
        self.get_logger().info(
            f'Camera FOV: {self._horizontal_fov:.3f}°W x '
            f'{self._vertical_fov:.3f}°H')

    def _on_image(self, image):
        if self._compressed:
            try:
                frame = self._bridge.compressed_imgmsg_to_cv2(
                    image, desired_encoding='passthrough')
                height, width = frame.shape[:2]
            except Exception as exc:
                self.get_logger().warning(
                    f'Could not decode compressed image: {exc}',
                    throttle_duration_sec=5.0)
                return
        else:
            width = image.width
            height = image.height

        if width <= 0 or height <= 0:
            self.get_logger().warning(
                'Skipping image with invalid dimensions',
                throttle_duration_sec=5.0)
            return

        frame_id = self._frame_id or image.header.frame_id
        camera_info = self._create_camera_info(width, height, image.header)
        camera_info.header.frame_id = frame_id
        image.header.frame_id = frame_id

        self._image_pub.publish(image)
        self._camera_info_pub.publish(camera_info)

    def _create_camera_info(self, width, height, header):
        focal_x = (width / 2.0) / math.tan(
            math.radians(self._horizontal_fov / 2.0))
        focal_y = (height / 2.0) / math.tan(
            math.radians(self._vertical_fov / 2.0))
        center_x = width / 2.0
        center_y = height / 2.0

        camera_info = CameraInfo()
        camera_info.header = header
        camera_info.width = width
        camera_info.height = height
        camera_info.distortion_model = 'plumb_bob'
        camera_info.d = [0.0] * 5
        camera_info.k = [
            focal_x, 0.0, center_x,
            0.0, focal_y, center_y,
            0.0, 0.0, 1.0,
        ]
        camera_info.r = [
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
        ]
        camera_info.p = [
            focal_x, 0.0, center_x, 0.0,
            0.0, focal_y, center_y, 0.0,
            0.0, 0.0, 1.0, 0.0,
        ]
        return camera_info


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = FakeCameraInfoNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()