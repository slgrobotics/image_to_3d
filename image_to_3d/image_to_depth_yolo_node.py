#!/usr/bin/env python3

"""ROS 2 bridge from camera images to HTTP depth and YOLO servers."""

import queue
import threading
from copy import deepcopy

import cv2
import numpy as np
import requests
import rclpy
from cv_bridge import CvBridge
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, CompressedImage, Image
from vision_msgs.msg import (
    Detection3D,
    Detection3DArray,
    ObjectHypothesisWithPose,
)

"""

This node subscribes to a raw or compressed image topic, sends the images to
HTTP depth and YOLO servers, publishes the resulting depth maps, and publishes
YOLO detections as Detection3DArray messages.

ros2 launch image_to_3d image_to_depth_node.launch.py

  or

ros2 run image_to_3d image_to_depth_yolo_node --ros-args \
    -p depth_server:=http://localhost:5001/depth \
    -p inference_server:=http://localhost:5002/detect

"""

class ImageToDepthAndYoloNode(Node):

    def __init__(self):
        super().__init__('image_to_depth_yolo_node')

        self.get_logger().info('Starting image_to_depth_yolo_node')

        self.declare_parameter(
            'input_topic', 'camera_3d/image_raw')
        self.declare_parameter('input_type', 'raw')  # raw or compressed
        self.declare_parameter(
            'camera_info_topic', 'camera_3d/camera_info')
        self.declare_parameter(
            'output_topic', 'camera_3d/depth/image_16UC1')
        self.declare_parameter(
            'camera_info_output_topic', 'camera_3d/depth/camera_info')
        self.declare_parameter(
            'depth_server', 'http://localhost:5001/depth')
        self.declare_parameter(
            'inference_server', 'http://localhost:5002/detect')
        self.declare_parameter(
            'detections_topic', 'camera_3d/detections')
        self.declare_parameter('request_timeout', 5.0)
        self.declare_parameter('queue_size', 1)

        input_topic = self.get_parameter('input_topic').value
        input_type = str(
            self.get_parameter('input_type').value).strip().lower()
        if input_type not in ('raw', 'compressed'):
            raise ValueError('input_type must be either raw or compressed')
        camera_info_topic = self.get_parameter('camera_info_topic').value
        output_topic = self.get_parameter('output_topic').value
        camera_info_output_topic = self.get_parameter(
            'camera_info_output_topic').value
        self._depth_server = self.get_parameter('depth_server').value
        self._inference_server = self.get_parameter('inference_server').value
        detections_topic = self.get_parameter('detections_topic').value
        self._input_compressed = input_type == 'compressed'
        self._request_timeout = float(
            self.get_parameter('request_timeout').value)
        queue_size = max(1, int(self.get_parameter('queue_size').value))

        self._depth_pub = self.create_publisher(Image, output_topic, 10)
        self._camera_info_pub = self.create_publisher(
            CameraInfo, camera_info_output_topic, 10)
        self._detections_pub = self.create_publisher(
            Detection3DArray, detections_topic, 10)
        self.create_subscription(
            CompressedImage if self._input_compressed else Image,
            input_topic, self._on_image, 10)
        self.create_subscription(
            CameraInfo, camera_info_topic, self._on_camera_info, 10)

        self._frames = queue.Queue(maxsize=queue_size)
        self._stop_event = threading.Event()
        self._session = requests.Session()
        self._bridge = CvBridge()
        self._camera_info_lock = threading.Lock()
        self._camera_info = None
        self._worker = threading.Thread(
            target=self._process_frames, daemon=True)
        self._worker.start()

        self.get_logger().info('Pipeline:')
        self.get_logger().info(f' - subscribing to:                  {input_topic}')
        self.get_logger().info(
            f' - input transport:                 {input_type}')
        self.get_logger().info(
            f' - subscribing to camera info:      {camera_info_topic}')
        self.get_logger().info(f' - converting via server at:        {self._depth_server}')
        self.get_logger().info(
            f' - detecting via server at:         {self._inference_server}')
        self.get_logger().info(f' - publishing depth images to:      {output_topic}')
        self.get_logger().info(
            f' - re-publishing depth camera info: {camera_info_output_topic}')
        self.get_logger().info(
            f' - publishing 3D detections to:     {detections_topic}')


    def _on_image(self, message):
        try:
            self._frames.put_nowait(message)
        except queue.Full:
            try:
                self._frames.get_nowait()
                self._frames.put_nowait(message)
            except queue.Empty:
                pass


    def _on_camera_info(self, message):
        with self._camera_info_lock:
            self._camera_info = message


    def _process_frames(self):
        while not self._stop_event.is_set():
            try:
                message = self._frames.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                if self._input_compressed:
                    request_data = bytes(message.data)
                    content_type = (
                        f'image/{message.format}'
                        if message.format else 'image/jpeg')
                else:
                    frame = self._bridge.imgmsg_to_cv2(
                        message, desired_encoding='bgr8')
                    encoded_ok, encoded = cv2.imencode('.jpg', frame)
                    if not encoded_ok:
                        raise RuntimeError('could not encode raw image as JPEG')
                    request_data = encoded.tobytes()
                    content_type = 'image/jpeg'

                response = self._session.post(
                    self._depth_server,
                    data=request_data,
                    headers={'Content-Type': content_type},
                    timeout=self._request_timeout,
                )
                response.raise_for_status()
                depth = cv2.imdecode(
                    np.frombuffer(response.content, dtype=np.uint8),
                    cv2.IMREAD_UNCHANGED,
                )
                if depth is None:
                    raise RuntimeError('depth server returned undecodable data')
                if depth.dtype != np.uint16 or depth.ndim != 2:
                    raise RuntimeError(
                        f'expected a single-channel uint16 depth map, got '
                        f'{depth.dtype} with shape {depth.shape}')

                response = self._session.post(
                    self._inference_server,
                    data=request_data,
                    headers={'Content-Type': content_type},
                    timeout=self._request_timeout,
                )
                response.raise_for_status()
                inference = response.json()
                detections = inference.get('detections')
                if not isinstance(detections, list):
                    raise RuntimeError(
                        'inference server response has no detections list')

                depth_message = self._bridge.cv2_to_imgmsg(
                    depth, encoding='16UC1')
                depth_message.header = message.header
                self._depth_pub.publish(depth_message)
                with self._camera_info_lock:
                    camera_info = deepcopy(self._camera_info)
                if camera_info is not None:
                    camera_info.header.stamp = depth_message.header.stamp
                    self._camera_info_pub.publish(camera_info)
                    detection_message = self._create_detection_array(
                        detections, depth, camera_info, depth_message.header)
                    self._detections_pub.publish(detection_message)
                else:
                    self.get_logger().warning(
                        'No camera info received yet; skipping depth camera '
                        'info and 3D detections',
                        throttle_duration_sec=5.0)
            except requests.RequestException as exc:
                self.get_logger().warning(
                    f'HTTP depth or inference request failed: {exc}',
                    throttle_duration_sec=5.0)
            except (RuntimeError, cv2.error, ValueError, KeyError) as exc:
                self.get_logger().warning(
                    f'Invalid depth or detection response: {exc}',
                    throttle_duration_sec=5.0)


    @staticmethod
    def _depth_at_pixel(depth, u, v):
        """Return the median valid depth around a pixel, in meters."""

        height, width = depth.shape
        x = min(max(int(round(u)), 0), width - 1)
        y = min(max(int(round(v)), 0), height - 1)
        radius = 2
        values = depth[
            max(0, y - radius):min(height, y + radius + 1),
            max(0, x - radius):min(width, x + radius + 1),
        ]
        valid = values[values > 0]
        if valid.size == 0:
            return None
        return float(np.median(valid)) / 1000.0


    def _create_detection_array(self, detections, depth, camera_info, header):
        """Project YOLO box centers into the camera optical frame."""

        fx, fy = camera_info.k[0], camera_info.k[4]
        cx, cy = camera_info.k[2], camera_info.k[5]
        if fx <= 0.0 or fy <= 0.0:
            raise RuntimeError('camera info has invalid focal lengths')

        source_width = camera_info.width or depth.shape[1]
        source_height = camera_info.height or depth.shape[0]
        depth_height, depth_width = depth.shape
        result = Detection3DArray()
        result.header = header

        for item in detections:
            bbox = item['bbox']
            pixel_x = (float(bbox['x1']) + float(bbox['x2'])) / 2.0
            pixel_y = (float(bbox['y1']) + float(bbox['y2'])) / 2.0
            depth_x = pixel_x * depth_width / source_width
            depth_y = pixel_y * depth_height / source_height
            z = self._depth_at_pixel(depth, depth_x, depth_y)
            if z is None:
                self.get_logger().warning(
                    f'No valid depth at detection center '
                    f'({pixel_x:.1f}, {pixel_y:.1f}); skipping detection',
                    throttle_duration_sec=5.0)
                continue

            x = (pixel_x - cx) * z / fx
            y = (pixel_y - cy) * z / fy
            width_pixels = abs(float(bbox['x2']) - float(bbox['x1']))
            height_pixels = abs(float(bbox['y2']) - float(bbox['y1']))
            detection_id = str(item.get('class_id', item.get('class_name', '')))
            class_id = str(item.get('class_name', item.get('class_id', '')))

            detection = Detection3D()
            detection.header = header
            detection.id = detection_id
            detection.bbox.center.position.x = x
            detection.bbox.center.position.y = y
            detection.bbox.center.position.z = z
            detection.bbox.center.orientation.w = 1.0
            detection.bbox.size.x = width_pixels * z / fx
            detection.bbox.size.y = height_pixels * z / fy
            detection.bbox.size.z = 0.3  # small thickness for 3D bounding box

            hypothesis = ObjectHypothesisWithPose()
            hypothesis.hypothesis.class_id = class_id
            hypothesis.hypothesis.score = float(item['confidence'])
            hypothesis.pose.pose.position.x = x
            hypothesis.pose.pose.position.y = y
            hypothesis.pose.pose.position.z = z
            hypothesis.pose.pose.orientation.w = 1.0
            detection.results.append(hypothesis)
            result.detections.append(detection)

        return result


    def destroy_node(self):
        self._stop_event.set()
        self._session.close()
        self._worker.join(timeout=1.0)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = ImageToDepthAndYoloNode()
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
