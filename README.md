Back to [Main Project Home](https://github.com/slgrobotics/articubot_one/wiki)

## Image to 3D ROS2 Package
**image_to_3d** is a ROS 2 package for converting monocular camera images into depth and derived 3D representations.
- It provides nodes for image-to-depth estimation and for converting depth images into *PointCloud2* and *LaserScan* messages.
- It also contains node that translates camera X,Y pixel coordinates to 3D coordinates.
- It uses *Depth Anything V2* AI model. A machine with Nvidia Geforce RTX 3060 or better is required (somewhere on LAN).

Contents:
- [Build and run](https://github.com/slgrobotics/image_to_3d#build-and-run)
- [Camera setup](https://github.com/slgrobotics/image_to_3d#camera-setup)
- [Fake CameraInfo node](https://github.com/slgrobotics/image_to_3d/blob/main/README.md#fake-camerainfo-node)
- [Depth Anything V2 HTTP Server](https://github.com/slgrobotics/image_to_3d#depth-anything-v2-http-server)
- [Image to Depth node](https://github.com/slgrobotics/image_to_3d#image-to-depth-node)
- [Depth To Laser Scan node](https://github.com/slgrobotics/image_to_3d#depth-to-laser-scan-node)
- [Producing PointCloud2 from Depth topic](https://github.com/slgrobotics/image_to_3d#producing-pointcloud2-from-depth-topic)
- [Calibrating Pointcloud](https://github.com/slgrobotics/image_to_3d#calibrating-pointcloud)

-----------------------------

### Build and run

> Your workstation is likely the best to install this package. Camera and robot stack (Nav2 etc.) can run anywhere on the LAN.

Place this package in your ROS 2 workspace's `src` directory:
```
mkdir -p ~/robot_ws/src
cd ~/robot_ws/src
git clone https://github.com/slgrobotics/image_to_3d.git
```

> **Check out** *~/robot_ws/src/image_to_3d/tests* directory

From the workspace root, with your ROS 2 environment sourced:
```bash
cd ~/robot_ws

colcon build
  or
colcon build --packages-select image_to_3d --symlink-install
```
Now you can run specific nodes as required.

> **Note:**
> - some examples below use *HuskyLens 2* camera for input and related [package](https://github.com/slgrobotics/huskylens2_ros2).
> - you can use any monocular camera as input. If your camera is calibrated (for a specific WxH resolution, like 640x480) your driver node will publish correct *CameraInfo*
> - if your camera driver node does not publish *CameraInfo* (or if it doesn't produce desired results) - use `image_to_3d/fake_camera_info_node.py`
> [node](https://github.com/slgrobotics/image_to_3d/blob/main/image_to_3d/fake_camera_info_node.py).

### Camera setup

> **Note:** some examples and images below mention *[HuskyLens 2](https://www.amazon.com/dp/B0H1Q77BTR)* camera and refer to [huskylens2_ros2](https://github.com/slgrobotics/huskylens2_ros2) package.

For a *Ubuntu 24.04* + *ROS 2 Jazzy* setup, you can start with [usb_cam](https://github.com/ros-drivers/usb_cam). 
It is a maintained ROS 2 driver for V4L cameras and works with typical  `/dev/video0` webcams.

It publishes the usual ROS camera topics and supports configuration of resolution, frame rate, pixel format, device,
and camera [calibration](https://docs.ros.org/en/kilted/p/camera_calibration/doc/tutorial_mono.html).

Install it:
```
sudo apt install ros-${ROS_DISTRO}-usb-cam
```

Run it:
```
ros2 run usb_cam usb_cam_node_exe --ros-args \
    -r __ns:=/camera \
    -p framerate:=10.0
```
This is how RQT shows camera topics:

<img alt="RQT shows webcam topics" src="https://github.com/user-attachments/assets/a71978de-6a35-4991-985f-3bedea5dc9b6" />

> **Note:**
> - the `-r __ns:=/camera` (the node namespace) becomes a prefix for all its topics
> - the */camera/image_raw/compressedDepth* topic is not really published for monocular webcams
> - the *framerate* does not have to be higher than what the *Depth Anything V2 HTTP Server* can process
> - use RQT Viewer plugin to confirm that both *raw* and *compressed* topics are showing up properly. You can also use:
> ```
> ros2 run image_view image_view --ros-args -r image:=/camera/image_raw -p image_transport:=compressed
> ```
> - this is how to use *[compressed transport](https://github.com/slgrobotics/robots_bringup/blob/main/Docs/Sensors/Camera.md#using-compressed-transport)*

### Fake *CameraInfo* node

The [fake_camera_info_node](https://github.com/slgrobotics/image_to_3d/blob/main/image_to_3d/fake_camera_info_node.py)
node is intended for cameras or image sources that do not provide their own
*CameraInfo*, allowing the image stream to be used by ROS 2 components that
require camera intrinsics, such as depth-image projection and 3D perception tools.

This node subscribes to a raw or compressed camera image, determines the image
dimensions, and republishes the image together with a synchronized CameraInfo
message.

In most cases you don't need to calibrate your camera - just figure out its actual horizontal and vertical
fields of view (*HFOV* and *VFOV*) in degrees. These could be different when using different resolution modes.

Launch it using a sample [launch file](https://github.com/slgrobotics/image_to_3d/blob/main/launch/fake_camera_info.launch.py):
```
cd ~/robot_ws
source install/setup.bash
ros2 launch image_to_3d fake_camera_info.launch.py camera_fov:=92.0,76.0
```

> **Note:**
> - The generated *CameraInfo* is an approximation based on the supplied field of view.
> - It does not replace a proper intrinsic camera [calibration](https://docs.ros.org/en/kilted/p/camera_calibration/doc/tutorial_mono.html),
> particularly for cameras with significant lens distortion.

### Depth Anything V2 HTTP Server

See this [guide](https://github.com/slgrobotics/articubot_one/wiki/Depth-Anything-V2) for information.

The *Depth Anything V2 HTTP Server* in the `depth_anything` [directory](https://github.com/slgrobotics/image_to_3d/blob/main/depth_anything/README.md)
takes an image and returns a depth map (as a PNG image).

It must be run in an environment with a GPU (CUDA) - normally a Python
"sandboxed" *virtual environment* with PyTorch installed.

> **Note:**
> - A machine with *Nvidia Geforce RTX 3060* or better is required.
> - You can run either *indoors* or *outdoors* model in a single server instance

You can run the following test in a *virtual environment*:
- `tests/test_depth.py`

Refer to [this guide](https://github.com/slgrobotics/image_to_3d/blob/main/depth_anything/README.md) for installation and use.

A ROS2 node or any other program can issue an HTTP POST request to this server
with an image.

The server loads the model once at startup, processes each input image,
performs inference, and returns the depth map as a 16-bit PNG image.

```    
     ROS 2 node / other client
                 │
                 │ HTTP POST
                 │ image/jpeg or image/png
                 ▼
    ┌────────────────────────────┐
    │ Depth Anything V2 server   │
    │                            │
    │ decode image               │
    │ preprocess                 │
    │ CUDA inference             │
    │ resize to input size       │
    │ meters → uint16 mm         │ 
    │   & Apply DEPTH_MULTIPLIER │
    │ encode PNG                 │
    └────────────┬───────────────┘
                 │
                 │ HTTP response
                 │ image/png
                 ▼
          16-bit depth map
```

The following tests interact with the server in a client role:
- `tests/test_depth_server.py`
- `tests/test_depth_server_gui.py`
- `tests/test_depth_webcam.py`

A stand-alone `tests/test_depth.py` can directly call Depth Anything V2 model (while running under a [virtual environment](https://github.com/slgrobotics/articubot_one/wiki/Depth-Anything-V2)).

### Image to Depth node

A universal *image_to_depth_node* is included in the package. It subscribes to an image topic and queries the *Depth Anything V2 server*, publishing its response as depth maps/images.

This node works with any node publishing compressed images.

Make sure that the Depth Anything V2 server is running, e.g.:
```
  cd ~/robot_ws/src/image_to_3d/depth_anything
  ... activate your Python 3 virtual environment ...
  ./depth_server.py
```

Run it (on the same machine as *Depth Anything V2 server* to minimize image traffic):
```
cd ~/robot_ws
source install/setup.bash

ros2 run image_to_3d image_to_depth_node

  or

ros2 run image_to_3d image_to_depth_node --ros-args -p depth_server:=http://127.0.0.1:5001/depth
```

Here is how it works when processing *HuskyLens 2* images:
```    
     ROS 2 image publishing node (HuskyLens 2 MCP Client)
                    │
                    │ 'huskylens/image/compressed' topic
                    ▼
     ROS 2 image_to_depth_node -----┐
                                    │ HTTP POST
                                    ▼
                        ┌──────────────────────────┐
                        │ Depth Anything V2 server │
                        └───────────┬──────────────┘
                                    ▼ HTTP response -  16-bit depth map
     ROS 2 image_to_depth_node -----┘
                 │  'camera_3d/depth/image' topic
                 ▼
        Any ROS2 subscribers
```

For example, this is how an image from [HuskyLens 2](https://github.com/slgrobotics/huskylens2_ros2) is transferred:

`huskylens/image/compressed` as came from *HuskyLens 2 MCP Server*:

<img width="757" height="567" alt="Screenshot from 2026-09-15 17-08-00" src="https://github.com/user-attachments/assets/866af907-b61e-4dff-a46e-b22270b31044" />

Depth image returned by *Depth Anything V2 server* and published by *image_to_depth_node* as, for example, `camera_3d/depth/image`:

<img width="757" height="567" alt="Screenshot from 2026-09-15 17-07-47" src="https://github.com/user-attachments/assets/bb1fea82-c46f-45af-97d7-a5b0faf03fe5" />

### Depth To Laser Scan Node

This node subscribes to *depth image* and *CameraInfo* topics and publishes a horizontal *LaserScan*. 
It selects valid depth samples within the configured height limits, projects them onto the horizontal X-Y plane,
and groups them into uniformly spaced angular scan bins.
Each scan bin reports the range to the nearest valid depth sample within that angular interval.

```
cd ~/robot_ws
source install/setup.bash
ros2 run image_to_3d depth_to_laserscan_node
```

<img alt="Depth to Laser Scan" src="https://github.com/user-attachments/assets/8ef8a1ad-f89f-4876-9c09-6159d0d71577" />

### Producing PointCloud2 from Depth topic

The standard ROS 2 package for this is [depth_image_proc](https://github.com/ros-perception/image_pipeline), specifically its *PointCloudXyzNode*. 
It takes a metric depth *sensor_msgs/Image* plus the corresponding *sensor_msgs/CameraInfo* and publishes *sensor_msgs/PointCloud2*.
The implementation supports 16UC1 depth images.

There is fair amount of [documentation](https://docs.ros.org/en/rolling/p/image_pipeline/) available.

The package can be installed from the binaries:
```
sudo apt install ros-${ROS_DISTRO}-image-pipeline
```

When using Depth Anything pipeline, the intended flow is:
```
     Camera Publisher Node ───────────────┐
             │                            │
             ▼                            │
       sensor_msgs/Image                  │
             ↓                            │
     ROS 2 client (image_to_depth_node)   │
             ↓ HTTP POST                  │
       Depth Anything server              │
             ↓                            │
       16-bit PNG, millimeters            │
             ↓ HTTP                       │
     ROS 2 client (image_to_depth_node)   │
             │                            │
             ▼                            ▼
      sensor_msgs/Image    sensor_msgs/CameraInfo
      (encoding: 16UC1)          ↓
             ↓                   ↓
      depth_image_proc::PointCloudXyzNode
             │
             ▼
      sensor_msgs/PointCloud2
```
> **Note:**
> - you don't need *HuskyLens 2* to implement this pipeline. Regular [cameras](https://github.com/slgrobotics/robots_bringup/blob/main/Docs/Sensors/Camera.md)
> and even webcams with their ROS2 driver nodes produce images and *CameraInfo* to feed the pipeline.
> - you need *CameraInfo*, not just the depth image. The conversion needs the *camera intrinsics fx, fy, cx, cy* to back-project each depth pixel (distance from camera) *(u,v,Z)* into 3D space *XYZ*
> - you can produce *synthetic CameraInfo* derived from camera field of view - use `image_to_3d/fake_camera_info_node.py`
> [node](https://github.com/slgrobotics/image_to_3d/blob/main/image_to_3d/fake_camera_info_node.py).
> - If you also want an *XYZRGB colored point cloud*, *depth_image_proc* has a *PointCloudXyzrgbNode*, which combines depth with the RGB image.
> - If you need to reduce your *CloudPoint2* to a *LaserScan* - follow [this guide](https://github.com/slgrobotics/robots_bringup/blob/main/Docs/Sensors/OAK-D_Lite.md#converting-pointcloud2-to-laserscan).
> Or just use *Depth To Laser Scan Node*

For HuskyLens 2 run conversion as follows:
```
cd ~/robot_ws
source install/setup.bash
ros2 launch image_to_3d point_cloud_node.launch.py
```

<img alt="PointCloud2 in RViz" src="https://github.com/user-attachments/assets/646f6037-8f22-4a00-a85c-cb862e898007" />

<img alt="PointCloud2 in RViz axis color" src="https://github.com/user-attachments/assets/752ef786-574f-41e9-82d1-50686b1652a9" />

----------------------

And, with *PointCloudXyzrgbNode*:
```
cd ~/robot_ws
source install/setup.bash
ros2 launch image_to_3d point_cloud_rgb_node.launch.py
```

<img alt="PointCloud2 in RViz RGB color" src="https://github.com/user-attachments/assets/39f565d6-7001-4ee3-a5ed-700c432bca81" />

<img alt="RQT_graph" src="https://github.com/user-attachments/assets/b4ccc447-899f-492b-885b-fa089bcce340" />

### Calibrating Pointcloud

When viewed in RViz2 over the one meter grid the pointcloud might be significantly distorted.

Values delivered by *depth_server.py* seem to depend on camera FOV, and need some scaling to be brought close to reality.

#### Calibration process

**Note:** You need to run four processes in different terminals (and also RViz2):
```
# "Depth Anything V2" HTTP server waits for an image and returns depth map image:
(venv) xxx@yyy:~/robot_ws/src/image_to_3d/depth_anything$ ./depth_server.py

# ROS2 node querying HuskyLens 2 MCP Server for image and detections:
xxx@yyy:~/husky_ws$ ros2 launch huskylens2_ros2 huskylens2_mcp.launch.py camera_module:="wide_angle"

# Note: you can use any other ROS2 camera node, make sure to remap topics properly

# always source the package:
cd ~/robot_ws
source install/setup.bash

# ROS2 node takes image and uses HTTP Server to convert camera image to depth map image:
xxx@yyy:~/robot_ws$ ros2 launch image_to_3d image_to_depth_node.launch.py

# ROS2 node to convert depth map image to PointCloud2:
xxx@yyy:~/robot_ws$ ros2 launch image_to_3d point_cloud_rgb_node.launch.py
```

If working with HuskyLens 2, the following line in `launch/huskylens2_mcp.launch.py` should match the position of your camera:
```
'--z', '0.57',    # Z translation in meters (camera height above ground)
```

1. Note some objects and the distance to them (depth dimensions) from the camera; adjust parameter below in `depth_server.py` while observing the scene in RViz2.

```
# experimental scale factor for HuskyLens 2 depth values:
DEPTH_MULTIPLIER = 1.15   # for HuskyLens 2 stock camera module
# DEPTH_MULTIPLIER = 0.5  # for HuskyLens 2 wide-angle camera module
```

2. When using different cameras, horizontal dimensions can also be distorted. Once the depth server is calibrated, 
note the distance between two objects at the same distance from the camera.

Adjust the `camera_module:="...,..."` values in `huskylens2_mcp_module` (launch, yaml) until that distance matches reality.
These are FOV values that directly affect calculated values in CameraInfo.

3. Round objects should be round, adjust the second value which is responsible for it.

**Note:** use "map" as *Fixed Frame* in RViz2.

> Wide Angle camera calibrated:
<img alt="Wide Angle calibrated" src="https://github.com/user-attachments/assets/f87a93e3-0528-4588-b2e8-717d1155b56d" />

---------------------

> Stock camera calibrated:
<img alt="Stock camera calibrated" src="https://github.com/user-attachments/assets/339f18de-ce2a-45fb-86bd-f50fdbc14359" />


-------------------------

Back to [Main Project Home](https://github.com/slgrobotics/articubot_one/wiki)


