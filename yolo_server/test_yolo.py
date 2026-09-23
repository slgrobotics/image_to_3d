#!/usr/bin/env python3

"""
Run real-time YOLO object detection on frames from a camera.

The script loads a YOLO model, reports detected objects and bounding boxes,
displays an annotated camera stream with inference timing, and uses CUDA when
available. Press ``q`` or ``Esc`` to stop the stream.

Prerequisites:
    - A machine with a CUDA-capable GPU and the appropriate drivers installed.
    - a webcam or other camera connected to the machine.
    - the script will open a window to display the annotated camera stream, so a graphical environment is required.

Preparation:
    mkdir -p ~/robot_ws/src/image_to_3d/yolo_server
    cd ~/robot_ws/src/image_to_3d/yolo_server
    python3 -m venv .venv
    source .venv/bin/activate
 
    # in the virtual environment, install the required packages:
    python -m pip install --upgrade pip
    pip install ultralytics
    
    # check that CUDA is available and the GPU is detected:
    python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
    # expect:
    #    True                        (CUDA available)
    #    NVIDIA GeForce RTX 3060 Ti  (or whatever GPU you have)
    
    # run a test inference to download the model and check that it works.
    # this will load OLO26s model, open the camera, and after a short delay
    # display the annotated stream in a window:
    yolo predict model=yolo26s.pt source=0 show=True device=0

Run it - it basically replicates the above command, but in a Python script that can be modified and extended:
    python3 test_yolo.py

"""

import time
import cv2
import torch

from ultralytics import YOLO


MODEL_NAME = "yolo26s.pt"
CAMERA_ID = 0
CONFIDENCE = 0.40


print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Load the model once.
model = YOLO(MODEL_NAME)

camera = cv2.VideoCapture(CAMERA_ID)

if not camera.isOpened():
    raise RuntimeError(f"Cannot open camera {CAMERA_ID}")

try:
    while True:
        ok, frame = camera.read()

        if not ok:
            print("Failed to read camera")
            break

        start = time.perf_counter()

        results = model.predict(
            frame,
            conf=CONFIDENCE,
            device=0,
            verbose=False,
        )

        inference_ms = (time.perf_counter() - start) * 1000.0

        result = results[0]

        # Print detections.
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            x1, y1, x2, y2 = box.xyxy[0].cpu().tolist()

            print(
                f"{result.names[class_id]:15s} "
                f"{confidence:.2f} "
                f"[{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]"
            )

        # Ultralytics generates an annotated OpenCV image.
        annotated = result.plot()

        cv2.putText(
            annotated,
            f"Inference: {inference_ms:.1f} ms",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.imshow("YOLO26 Object Detection", annotated)

        key = cv2.waitKey(1) & 0xFF

        if key == 27 or key == ord("q"):
            break

except KeyboardInterrupt:
    print("\nStopping YOLO detection...")

finally:
    camera.release()
    cv2.destroyAllWindows()
