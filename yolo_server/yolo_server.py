#!/usr/bin/env python3

"""HTTP server for YOLO object detection.

The server accepts a JPEG or PNG image at ``POST /detect`` and returns the
detections as JSON. The YOLO model is loaded once at startup.

Run this script from the YOLO virtual environment:

	python3 yolo_server.py

Example request:

	curl -X POST \\
		-H "Content-Type: image/jpeg" \\
		--data-binary @image.jpg \\
		http://localhost:5002/detect
"""

import time

import cv2
import numpy as np
import torch
from fastapi import FastAPI, HTTPException, Request
from ultralytics import YOLO


MODEL_NAME = "yolo26s.pt"
HOST = "localhost"
PORT = 5002
CONFIDENCE = 0.40
device = 0 if torch.cuda.is_available() else "cpu"
device_name = (
	torch.cuda.get_device_name(0)
	if torch.cuda.is_available()
	else "cpu"
)


print(f"MODEL_NAME: {MODEL_NAME}", flush=True)
print(f"Device: {device_name}", flush=True)
if torch.cuda.is_available():
	print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)

print("Loading model...", flush=True)
model = YOLO(MODEL_NAME)
print("Model loaded.", flush=True)


def detect_objects(image):
	"""Run YOLO inference and convert detections into JSON-compatible data."""

	start = time.perf_counter()
	results = model.predict(
		image,
		conf=CONFIDENCE,
		device=device,
		verbose=False,
	)
	inference_ms = (time.perf_counter() - start) * 1000.0

	result = results[0]
	detections = []

	for box in result.boxes:
		class_id = int(box.cls[0])
		confidence = float(box.conf[0])
		x1, y1, x2, y2 = box.xyxy[0].cpu().tolist()

		detections.append({
			"class_id": class_id,
			"class_name": result.names[class_id],
			"confidence": confidence,
			"bbox": {
				"x1": x1,
				"y1": y1,
				"x2": x2,
				"y2": y2,
			},
		})

	return detections, inference_ms


app = FastAPI(
	title="YOLO Object Detection Server",
	description="Accepts an image and returns YOLO detections as JSON.",
	version="1.0",
)


@app.get("/")
def root():
	"""Return basic server information."""

	return {
		"service": "YOLO Object Detection",
		"model": MODEL_NAME,
		"device": device_name,
		"endpoint": "/detect",
	}


@app.get("/health")
def health():
	"""Return the server health status."""

	return {
		"status": "ok",
		"model": MODEL_NAME,
		"device": device_name,
	}


@app.post("/detect")
async def detect_endpoint(request: Request):
	"""Accept an encoded image and return its YOLO detections as JSON."""

	request_start = time.perf_counter()
	image_bytes = await request.body()

	if not image_bytes:
		raise HTTPException(status_code=400, detail="Empty image request")

	image = cv2.imdecode(
		np.frombuffer(image_bytes, dtype=np.uint8),
		cv2.IMREAD_COLOR,
	)

	if image is None:
		raise HTTPException(
			status_code=400,
			detail="Unable to decode image; send JPEG or PNG bytes",
		)

	height, width = image.shape[:2]

	try:
		detections, inference_ms = detect_objects(image)
	except Exception as exc:
		print(f"Inference failed: {exc}", flush=True)
		raise HTTPException(
			status_code=500,
			detail=f"YOLO inference failed: {exc}",
		)

	total_ms = (time.perf_counter() - request_start) * 1000.0

	print(
		f"{width}x{height}  "
		f"detections={len(detections)}  "
		f"inference={inference_ms:.1f} ms  "
		f"total={total_ms:.1f} ms",
		flush=True,
	)

	return {
		"model": MODEL_NAME,
		"image": {
			"width": width,
			"height": height,
		},
		"detections": detections,
		"inference_ms": inference_ms,
		"total_ms": total_ms,
	}


if __name__ == "__main__":
	import uvicorn

	print(f"Starting YOLO server at http://{HOST}:{PORT}", flush=True)
	uvicorn.run(app, host=HOST, port=PORT, log_level="info")
