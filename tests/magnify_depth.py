#!/usr/bin/env python3

"""
Display a depth image and magnify a local 50x50 area under the mouse.

The main image is shown as grayscale, without color coding.
When the mouse moves, we compute the min and max depth values in the local 50x50 neighborhood, 
then normalize just that neighborhood to the full 0..255 grayscale range to amplify
relative differences in the local depth field.

cd /home/sergei/husky_ws/src/image_to_3d
python3 tests/magnify_depth.py

"""

from pathlib import Path

import cv2
import numpy as np


IMAGE_PATH = Path(__file__).resolve().parent / 'received_depth.png'
WINDOW_NAME = 'Depth magnifier'
PATCH_HALF = 25
PATCH_SIZE = PATCH_HALF * 2


def normalize_local_patch(patch: np.ndarray) -> np.ndarray:
    """Stretch a local patch to full dynamic range for local contrast enhancement."""
    patch_f = patch.astype(np.float32)
    vmin = float(patch_f.min())
    vmax = float(patch_f.max())
    if vmax <= vmin:
        return np.zeros_like(patch_f, dtype=np.uint8)
    normalized = (patch_f - vmin) / (vmax - vmin + 1e-6)
    return np.clip(normalized * 255.0, 0, 255).astype(np.uint8)


def draw_magnifier(frame: np.ndarray, x: int, y: int, depth: np.ndarray) -> np.ndarray:
    """Draw a 50x50 local enhanced patch centered on the mouse position."""
    x0 = max(0, x - PATCH_HALF)
    y0 = max(0, y - PATCH_HALF)
    x1 = min(depth.shape[1], x + PATCH_HALF)
    y1 = min(depth.shape[0], y + PATCH_HALF)

    if x1 <= x0 or y1 <= y0:
        return frame

    patch = depth[y0:y1, x0:x1]
    local_enhanced = normalize_local_patch(patch)

    # Fill a local 50x50 region under the pointer with the remapped values.
    roi_y0 = max(0, y - PATCH_HALF)
    roi_x0 = max(0, x - PATCH_HALF)
    roi_y1 = min(frame.shape[0], y + PATCH_HALF)
    roi_x1 = min(frame.shape[1], x + PATCH_HALF)

    try:
        frame_roi = frame[roi_y0:roi_y1, roi_x0:roi_x1]
        if frame_roi.shape[:2] != local_enhanced.shape[:2]:
            # If the patch is clipped at the border, resize to fit exactly.
            local_enhanced = cv2.resize(
                local_enhanced,
                (frame_roi.shape[1], frame_roi.shape[0]),
                interpolation=cv2.INTER_NEAREST,
            )
        frame[roi_y0:roi_y1, roi_x0:roi_x1] = local_enhanced
    except Exception:
        pass

    cv2.rectangle(
        frame,
        (x0, y0),
        (x1 - 1, y1 - 1),
        (255, 255, 255),
        1,
    )
    cv2.putText(
        frame,
        f'local range: {patch.min()}..{patch.max()}',
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    return frame


def on_mouse(event, x, y, flags, param):
    if event in (cv2.EVENT_MOUSEMOVE, cv2.EVENT_LBUTTONDOWN):
        param['x'] = x
        param['y'] = y


def main():
    depth = cv2.imread(str(IMAGE_PATH), cv2.IMREAD_ANYDEPTH)
    if depth is None:
        raise FileNotFoundError(f'Could not open {IMAGE_PATH}')

    if depth.ndim == 2:
        display = depth.astype(np.float32)
    else:
        display = cv2.cvtColor(depth, cv2.COLOR_BGR2GRAY).astype(np.float32)

    if display.dtype != np.uint8:
        # Keep the image in a standard grayscale format for display.
        display = np.clip(display, 0, 65535)
        display = (display / max(1.0, display.max()) * 255.0).astype(np.uint8)

    state = {'x': display.shape[1] // 2, 'y': display.shape[0] // 2}

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse, state)

    while True:
        image = display.copy()
        x = state['x']
        y = state['y']

        if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
            image = draw_magnifier(image, x, y, depth if depth.ndim == 2 else cv2.cvtColor(depth, cv2.COLOR_BGR2GRAY))

        cv2.imshow(WINDOW_NAME, image)
        key = cv2.waitKey(30) & 0xFF
        if key in (27, ord('q')):
            break

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
