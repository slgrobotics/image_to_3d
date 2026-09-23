
Back to [Package README](https://github.com/slgrobotics/image_to_3d#depth-anything-v2-http-server)

## Running HTTP Depth Server 

> A machine with **Nvidia Geforce RTX 3060** or better is required.

> Clients (including ROS nodes) can be anywhere on the LAN

Install *Python virtual environment*:

```
sudo apt install python3.14-venv

cd ~/robot_ws/src/image_to_3d/depth_anything
python3 -m venv venv
source venv/bin/activate
```
# YOLO Object Detection

This directory contains two YOLO programs:

- `yolo_server.py` runs an HTTP server that accepts an image and returns object
   detections as JSON.
- `test_yolo.py` runs local real-time detection from a camera and displays an
   annotated OpenCV window.

Both scripts use the `yolo26s.pt` model and a confidence threshold of `0.40`.

## Setup

Create and activate a virtual environment in this directory:

```bash
cd ~/husky_ws/src/image_to_3d/yolo_server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install the required packages:

```bash
pip install torch torchvision ultralytics fastapi uvicorn opencv-python numpy
```

The scripts use CUDA when it is available. Verify the PyTorch installation with:

```bash
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

The model file must be available as `yolo26s.pt` in the working directory. If
it is not present, Ultralytics may download it when the model is initialized.

## HTTP Server

Start the server from this directory:

```bash
source .venv/bin/activate
python3 yolo_server.py
```

The server listens at `http://localhost:5002`.

### Endpoints

`GET /` returns basic service information.

`GET /health` returns the server health status.

`POST /detect` accepts JPEG or PNG image bytes in the request body and returns
JSON. For example:

```bash
curl -X POST \
      -H "Content-Type: image/jpeg" \
      --data-binary @image.jpg \
      http://localhost:5002/detect
```

Example response:

```json
{
   "model": "yolo26s.pt",
   "image": {
      "width": 1920,
      "height": 1080
   },
   "detections": [
      {
         "class_id": 0,
         "class_name": "person",
         "confidence": 0.91,
         "bbox": {
            "x1": 412.5,
            "y1": 118.0,
            "x2": 892.25,
            "y2": 1012.75
         }
      }
   ],
   "inference_ms": 42.7,
   "total_ms": 45.1
}
```

Bounding-box coordinates are pixel coordinates in the input image. An image
with no detections returns an empty `detections` array. Empty or invalid image
requests return HTTP `400`; inference failures return HTTP `500`.

## Camera Test

`test_yolo.py` is a standalone local test. It opens camera `0`, runs detection
continuously, prints each detection, overlays inference timing, and displays
the annotated stream:

```bash
source .venv/bin/activate
python3 test_yolo.py
```

Press `q` or `Esc` to stop. `Ctrl+C` also shuts down cleanly and releases the
camera.

With the virtual environment activated install *PyTorch*:

```
python -m pip install --upgrade pip
pip install torch torchvision
```

Check *PyTorch* installation:
```
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')"
   PyTorch: 2.14.0+cu130
   CUDA: True
   GPU: NVIDIA GeForce RTX 3060 Ti
```

More installs:
```
pip install "transformers>=4.45" pillow opencv-python
pip install fastapi uvicorn

```

Run the server:
```
./depth_server.py

```

It should be ready to take HTTP/POST images and will return depth maps/images in PNG uint_16 format, ready for ROS2 processing.

URL: http://localhost:5001/

> Check out `~/robot_ws/src/image_to_3d/tests` directory

The following tests interact with the server in a client role:

- tests/test_depth_server.py
- tests/test_depth_server_gui.py
- tests/test_depth_webcam.py

A stand-alone `tests/test_depth.py` can directly call Depth Anything V2 model (while running under a virtual environment).

-------------------------

Back to [Package README](https://github.com/slgrobotics/image_to_3d#depth-anything-v2-http-server)

Back to [Main Project Home](https://github.com/slgrobotics/articubot_one/wiki)
