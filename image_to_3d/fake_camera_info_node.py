#!/usr/bin/env python3

"""
Publish images with synthetic CameraInfo derived from camera field of view.

The node is intended for cameras or image sources that do not provide their own
CameraInfo, allowing the image stream to be used by ROS 2 components that
require camera intrinsics, such as depth-image projection and 3D perception
tools.

This node subscribes to a raw or compressed camera image, determines the image
dimensions, and republishes the image together with a synchronized CameraInfo
message.

Camera intrinsics are calculated from the configured horizontal and vertical
fields of view (HFOV and VFOV) using a pinhole camera model. The optical center
is assumed to be at the center of the image, and lens distortion is assumed to
be zero.

Both raw and compressed image topics are supported independently for input and
output.

Parameters:
  camera_fov:
    Horizontal and vertical field of view in degrees, specified as
    "HFOV,VFOV".

input_topic:
    Input camera image topic.

output_topic:
    Republished image topic synchronized with CameraInfo.

camera_info_topic:
    Output CameraInfo topic.

input_type:
    Input image type: "raw" or "compressed".

output_type:
    Output image type: "raw" or "compressed".

frame_id:
    Optional frame ID override. If empty, the input image frame ID is used.

Note:
    The generated CameraInfo is an approximation based on the supplied field
    of view. It does not replace a proper intrinsic camera calibration,
    particularly for cameras with significant lens distortion.
"""


import math

import rclpy
from cv_bridge import CvBridge
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, CompressedImage, Image


def parse_fov(value) -> tuple[float, float]:
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


def parse_message_type(value, field_name) -> bool:
    normalized = str(value).strip().lower()
    if normalized not in ('raw', 'compressed'):
        raise ValueError(f'{field_name} must be either raw or compressed')
    return normalized == 'compressed'


class FakeCameraInfoNode(Node):

    def __init__(self):
        super().__init__('fake_camera_info_node')

        self.get_logger().info('Starting fake_camera_info_node')

        self.declare_parameter('camera_fov', '92.0,76.0')
        self.declare_parameter('input_topic',  'camera/image_raw/compressed')
        self.declare_parameter('input_type',   'compressed')
        self.declare_parameter('output_topic', 'camera_3d/image_raw')
        self.declare_parameter('output_type',  'raw')
        self.declare_parameter('camera_info_topic', 'camera_3d/camera_info')
        self.declare_parameter('frame_id', '')

        self._horizontal_fov, self._vertical_fov = parse_fov(
            self.get_parameter('camera_fov').value)
        input_topic = str(self.get_parameter('input_topic').value)
        output_topic = str(self.get_parameter('output_topic').value)
        camera_info_topic = str(
            self.get_parameter('camera_info_topic').value)
        input_type = parse_message_type(
            self.get_parameter('input_type').value, 'input_type')
        output_type = parse_message_type(
            self.get_parameter('output_type').value, 'output_type')
        self._frame_id = str(self.get_parameter('frame_id').value)

        self._input_compressed = input_type
        self._output_compressed = output_type

        input_msg_type = CompressedImage if self._input_compressed else Image
        output_msg_type = CompressedImage if self._output_compressed else Image
        self._image_pub = self.create_publisher(
            output_msg_type, output_topic, 10)

        self._camera_info_pub = self.create_publisher(
            CameraInfo, camera_info_topic, 10)
        self._bridge = CvBridge()

        self.create_subscription(
            input_msg_type, input_topic, self._on_image,
            qos_profile_sensor_data)

        self.get_logger().info(
            f'Camera FOV: {self._horizontal_fov:.3f}°W x '
            f'{self._vertical_fov:.3f}°H')
        self.get_logger().info(
            f'Input:  {input_topic}  transport: {"compressed" if self._input_compressed else "raw"}')
        self.get_logger().info(
            f'Output: {output_topic}  transport: {"compressed" if self._output_compressed else "raw"}  '
            f'with CameraInfo on {camera_info_topic}')

    def _on_image(self, image):
        if self._input_compressed:
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
            try:
                frame = self._bridge.imgmsg_to_cv2(
                    image, desired_encoding='passthrough')
            except Exception as exc:
                self.get_logger().warning(
                    f'Could not convert raw image: {exc}',
                    throttle_duration_sec=5.0)
                return
            height, width = frame.shape[:2]

        if width <= 0 or height <= 0:
            self.get_logger().warning(
                'Skipping image with invalid dimensions',
                throttle_duration_sec=5.0)
            return

        frame_id = self._frame_id or image.header.frame_id
        camera_info = self._create_camera_info(width, height, image.header)
        camera_info.header.frame_id = frame_id

        output_image = self._build_output_image(frame, image)
        output_image.header.frame_id = frame_id
        self._image_pub.publish(output_image)
        self._camera_info_pub.publish(camera_info)

    def _build_output_image(self, frame, image) -> Image | CompressedImage:
        if not self._input_compressed and not self._output_compressed:
            return image

        if self._output_compressed:
            output_image = self._bridge.cv2_to_compressed_imgmsg(
                frame, dst_format='jpeg')
            output_image.header = image.header
            return output_image

        output_image = self._bridge.cv2_to_imgmsg(
            frame, encoding=self._raw_encoding(frame))
        output_image.header = image.header
        return output_image

    @staticmethod
    def _raw_encoding(frame):
        channels = 1 if frame.ndim == 2 else frame.shape[2]
        if frame.dtype == 'uint8':
            encodings = {1: 'mono8', 3: 'bgr8', 4: 'bgra8'}
        elif frame.dtype == 'uint16':
            encodings = {1: 'mono16', 3: 'bgr16', 4: 'bgra16'}
        else:
            raise ValueError(
                f'Unsupported raw image dtype for ROS encoding: {frame.dtype}')

        try:
            return encodings[channels]
        except KeyError:
            raise ValueError(
                f'Unsupported raw image channel count: {channels}') from None

    def _create_camera_info(self, width, height, header) -> CameraInfo:
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
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()