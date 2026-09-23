#!/usr/bin/env python3

"""Send webcam frames to the YOLO HTTP server and display its detections.

The client sends one JPEG frame at a time, waiting for the response before
capturing and sending the next frame. This prevents requests from accumulating
when inference takes longer than the camera frame rate.

Press ``q`` or ``Esc`` to stop.
"""

import time

import cv2
import requests


SERVER = "http://localhost:5002/detect"
CAMERA_ID = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
JPEG_QUALITY = 90
REQUEST_TIMEOUT = 5.0


def draw_detection(frame, detection):
    """Draw one server detection on the camera frame."""

    try:
        class_name = str(detection["class_name"])
        confidence = float(detection["confidence"])
        bbox = detection["bbox"]
        x1 = int(round(float(bbox["x1"])))
        y1 = int(round(float(bbox["y1"])))
        x2 = int(round(float(bbox["x2"])))
        y2 = int(round(float(bbox["y2"])))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid detection returned by server: {exc}") from exc

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    label = f"{class_name}: {confidence:.2f}"
    text_y = max(y1 - 10, 20)
    cv2.putText(
        frame,
        label,
        (x1, text_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )


def main():
    print(f"YOLO server: {SERVER}")
    print(f"Opening camera {CAMERA_ID}...")

    camera = cv2.VideoCapture(CAMERA_ID)
    if not camera.isOpened():
        raise RuntimeError(f"Unable to open camera {CAMERA_ID}")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    actual_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = camera.get(cv2.CAP_PROP_FPS)
    print(f"Camera: {actual_width}x{actual_height} @ {actual_fps:.1f} FPS")

    window_name = "YOLO HTTP Object Detection"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, CAMERA_WIDTH, CAMERA_HEIGHT)

    frame_count = 0
    session = requests.Session()

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("Camera capture failed.")
                break

            frame_count += 1

            encode_start = time.perf_counter()
            success, jpeg = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY],
            )
            encode_ms = (time.perf_counter() - encode_start) * 1000.0

            if not success:
                print(f"Frame {frame_count}: JPEG encoding failed.")
                continue

            request_start = time.perf_counter()
            try:
                response = session.post(
                    SERVER,
                    data=jpeg.tobytes(),
                    headers={"Content-Type": "image/jpeg"},
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                payload = response.json()
            except requests.Timeout:
                print(
                    f"Frame {frame_count}: server timeout after "
                    f"{REQUEST_TIMEOUT:.1f} seconds"
                )
                continue
            except requests.RequestException as exc:
                print(f"Frame {frame_count}: HTTP error: {exc}")
                time.sleep(0.5)
                continue
            except ValueError as exc:
                print(f"Frame {frame_count}: invalid JSON response: {exc}")
                continue

            round_trip_ms = (time.perf_counter() - request_start) * 1000.0

            if not isinstance(payload, dict):
                print(f"Frame {frame_count}: response is not a JSON object")
                continue

            detections = payload.get("detections")
            if not isinstance(detections, list):
                print(f"Frame {frame_count}: response has no detections list")
                continue

            try:
                for detection in detections:
                    draw_detection(frame, detection)
            except ValueError as exc:
                print(f"Frame {frame_count}: {exc}")
                continue

            inference_ms = float(payload.get("inference_ms", 0.0))
            server_total_ms = float(payload.get("total_ms", 0.0))
            client_fps = 1000.0 / round_trip_ms if round_trip_ms > 0 else 0.0

            cv2.putText(
                frame,
                f"Detections: {len(detections)}  "
                f"Inference: {inference_ms:.1f} ms  "
                f"HTTP: {round_trip_ms:.1f} ms",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"Server total: {server_total_ms:.1f} ms  "
                f"Client: {client_fps:.1f} FPS  Press q or Esc to exit",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(window_name, frame)

            print(
                f"{frame_count:5d}  "
                f"JPEG={encode_ms:5.1f} ms  "
                f"HTTP={round_trip_ms:6.1f} ms  "
                f"inference={inference_ms:5.1f} ms  "
                f"detections={len(detections)}"
            )

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                break

    except KeyboardInterrupt:
        print("\nStopping YOLO webcam test...")
    finally:
        camera.release()
        session.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
