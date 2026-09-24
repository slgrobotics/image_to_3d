
Back to [Package README](https://github.com/slgrobotics/image_to_3d#depth-anything-v2-http-server)

## YOLO Object Detection - using HTTP Server

> **Note:** Clients (including ROS nodes) can be anywhere on the LAN

### Setup

This directory contains two programs:

- `yolo_server.py` runs an HTTP server that accepts an image and returns object detections as JSON.
- `test_yolo.py` runs local real-time detection from a camera (webcam) and displays an annotated OpenCV window.

Both scripts use the `yolo26s.pt` model and a confidence threshold of `0.40`.

**Prerequisites:**
- A machine with a CUDA-capable GPU and the appropriate drivers installed.
- a webcam or other camera connected to the machine.
- the test script will open a window to display the annotated camera stream, so a graphical environment is desirable.

**Preparation:**

If you haven't done it yet, place this package in your ROS 2 workspace's src directory:
```
mkdir -p ~/robot_ws/src
cd ~/robot_ws/src
git clone https://github.com/slgrobotics/image_to_3d.git
```
Create and activate Python virtual environment:
```
cd ~/robot_ws/src/image_to_3d/yolo_server
python3 -m venv venv_yolo
source venv_yolo/bin/activate
```

**in the virtual environment, install the required packages:**
```
python -m pip install --upgrade pip
pip install torch torchvision ultralytics fastapi uvicorn opencv-python numpy "transformers>=4.45" pillow
```

**check that CUDA is available and the GPU is detected:**
The scripts use CUDA when it is available. Verify the PyTorch installation with:
```bash
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

# Expect:
#    PyTorch: 2.14.0+cu130
#    CUDA: True                       (CUDA available)
#    GPU: NVIDIA GeForce RTX 3060 Ti  (or whatever GPU you have)
```

**run a test inference to download the model and check that it works**
this will load OLO26s model, open the camera, and after a short delay
display the annotated stream in a window:
```
yolo predict model=yolo26s.pt source=0 show=True device=0
```

### Camera/Webcam Test

`test_yolo.py` is a standalone local test. It opens camera `0` (e.g. a webcam), runs detection
continuously, prints each detection, overlays inference timing, and displays the annotated stream:

```bash
cd ~/robot_ws/src/image_to_3d/yolo_server
source /bin/activate
python3 test_yolo.py
```

Press `q` or `Esc` to stop. `Ctrl+C` also shuts down cleanly and releases the camera.

<img alt="test_yolo_webcam" src="https://github.com/user-attachments/assets/35581ae4-cce2-47f0-89d6-21646aa8ebd2" />

### Running Image Inference HTTP Server 

> **Note:** The model file must be available as `yolo26s.pt` in the working directory. If
> it is not present, Ultralytics may download it when the model is initialized.

Start the server:

```bash
cd ~/robot_ws/src/image_to_3d/yolo_server
source /bin/activate
python3 yolo_server.py
```

It should be ready to take HTTP/POST images and will return depth maps/images in PNG uint_16 format, ready for ROS2 processing.

The server listens at `http://localhost:5002`.

#### Endpoints:
- `GET /` returns basic service information:
  - `{"service":"YOLO Object Detection","model":"yolo26s.pt","device":"NVIDIA GeForce RTX 3060 Ti","endpoint":"/detect"}`
- `GET /health` returns the server health status:
  - `{"status":"ok","model":"yolo26s.pt","device":"NVIDIA GeForce RTX 3060 Ti"}`
- `POST /detect` accepts JPEG or PNG image bytes in the request body and returns JSON. For example:

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

- Bounding-box coordinates are pixel coordinates in the input image.
- An image with no detections returns an empty `detections` array.
- Empty or invalid image requests return HTTP `400`.
- Inference failures return HTTP `500`.

### HTTP Client test

> Check out `~/robot_ws/src/image_to_3d/tests` directory

The following test interacts with the server in a client role. With the server started (in a *virtual environment*), run the HTTP client in a regular terminal (outside of the virtual environment):
```
tests/test_yolo_server.py
```

It retrieves images from a webcam and sends them to the Image Inference HTTP Server, displaying the returned results in a window.

```
cd ~/robot_ws/src/image_to_3d/tests$ python3 test_yolo_webcam.py
```

<img width="1199" height="672" alt="Screenshot from 2026-09-23 17-08-37" src="https://github.com/user-attachments/assets/6fa07073-67a5-48b8-ac68-e54bbd66e85d" />

-------------------------

Back to [Package README](https://github.com/slgrobotics/image_to_3d#depth-anything-v2-http-server)

Back to [Main Project Home](https://github.com/slgrobotics/articubot_one/wiki)
