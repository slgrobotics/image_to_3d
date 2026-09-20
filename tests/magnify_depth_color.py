#!/usr/bin/env python3

"""
Display a depth image and magnify a local 50x50 area under the mouse using color mapping.

The main image is shown as grayscale, without color coding.
When the mouse moves, we compute the min and max depth values in the local 50x50 neighborhood, 
then normalize just that neighborhood to the full 0..255 grayscale or color range to amplify
relative differences in the local depth field.

cd ~/robot_ws/src/image_to_3d/tests
python3 magnify_depth_color.py
python3 magnify_depth_color.py --color
python3 magnify_depth_color.py --color --colormap turbo
python3 magnify_depth_color.py --color --colormap jet
python3 magnify_depth_color.py --color --colormap inferno
python3 magnify_depth_color.py --color --colormap viridis
python3 magnify_depth_color.py --color --colormap plasma

"""

from pathlib import Path

import argparse

import cv2
import numpy as np


IMAGE_PATH = Path(__file__).resolve().parent / 'received_depth.png'
WINDOW_NAME = 'Depth magnifier'
PATCH_HALF = 25
PATCH_SIZE = PATCH_HALF * 2


def normalize_depth_image(depth: np.ndarray, percentile: float = 1.0) -> np.ndarray:
    """Normalize the full depth image to 0..255 for display."""
    depth_f = depth.astype(np.float32)
    valid = depth_f[depth_f > 0]
    if valid.size == 0:
        return np.zeros_like(depth_f, dtype=np.uint8)
    lo = float(np.percentile(valid, percentile))
    hi = float(np.percentile(valid, 100.0 - percentile))
    if hi <= lo:
        hi = float(valid.max())
        lo = float(valid.min())
    if hi <= lo:
        return np.zeros_like(depth_f, dtype=np.uint8)
    normalized = np.clip((depth_f - lo) / (hi - lo), 0.0, 1.0)
    return (normalized * 255.0).astype(np.uint8)


def apply_distance_colormap(gray: np.ndarray, colormap: int) -> np.ndarray:
    """Apply a common distance-friendly colormap to a grayscale depth image."""
    if gray.ndim == 3:
        return gray
    return cv2.applyColorMap(gray, colormap)


def normalize_local_patch(patch: np.ndarray) -> np.ndarray:
    """Stretch a local patch to full dynamic range for local contrast enhancement."""
    patch_f = patch.astype(np.float32)
    valid = patch_f[patch_f > 0]
    if valid.size == 0:
        return np.zeros_like(patch_f, dtype=np.uint8)
    vmin = float(valid.min())
    vmax = float(valid.max())
    if vmax <= vmin:
        return np.zeros_like(patch_f, dtype=np.uint8)
    normalized = (patch_f - vmin) / (vmax - vmin + 1e-6)
    return np.clip(normalized * 255.0, 0, 255).astype(np.uint8)


def draw_magnifier(frame: np.ndarray, x: int, y: int, depth: np.ndarray, use_color: bool, colormap: int) -> np.ndarray:
    """Draw a 50x50 local enhanced patch centered on the mouse position."""
    x0 = max(0, x - PATCH_HALF)
    y0 = max(0, y - PATCH_HALF)
    x1 = min(depth.shape[1], x + PATCH_HALF)
    y1 = min(depth.shape[0], y + PATCH_HALF)

    if x1 <= x0 or y1 <= y0:
        return frame

    patch = depth[y0:y1, x0:x1]
    local_enhanced = normalize_local_patch(patch)
    if use_color:
        local_enhanced = apply_distance_colormap(local_enhanced, colormap)

    roi_y0 = max(0, y - PATCH_HALF)
    roi_x0 = max(0, x - PATCH_HALF)
    roi_y1 = min(frame.shape[0], y + PATCH_HALF)
    roi_x1 = min(frame.shape[1], x + PATCH_HALF)

    try:
        frame_roi = frame[roi_y0:roi_y1, roi_x0:roi_x1]
        if frame_roi.shape[:2] != local_enhanced.shape[:2]:
            local_enhanced = cv2.resize(
                local_enhanced,
                (frame_roi.shape[1], frame_roi.shape[0]),
                interpolation=cv2.INTER_NEAREST,
            )
        if use_color:
            frame[roi_y0:roi_y1, roi_x0:roi_x1] = local_enhanced
        else:
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


def build_depth_display(depth: np.ndarray, use_color: bool, colormap: int) -> np.ndarray:
    if depth.ndim == 2:
        gray = normalize_depth_image(depth)
        if use_color:
            return apply_distance_colormap(gray, colormap)
        return gray
    gray = cv2.cvtColor(depth, cv2.COLOR_BGR2GRAY)
    if use_color:
        return apply_distance_colormap(normalize_depth_image(gray), colormap)
    return normalize_depth_image(gray)


def main():
    parser = argparse.ArgumentParser(description='Display a depth image with a hover magnifier.')
    parser.add_argument('--color', action='store_true', help='show the whole image and magnified patch in color')
    parser.add_argument(
        '--colormap',
        type=str,
        default='turbo',
        choices=['turbo', 'jet', 'inferno', 'viridis', 'plasma'],
        help='OpenCV colormap for distance-color visualization',
    )
    args = parser.parse_args()

    colormap_map = {
        'turbo': cv2.COLORMAP_TURBO,
        'jet': cv2.COLORMAP_JET,
        'inferno': cv2.COLORMAP_INFERNO,
        'viridis': cv2.COLORMAP_VIRIDIS,
        'plasma': cv2.COLORMAP_PLASMA,
    }
    colormap = colormap_map[args.colormap]
    use_color = args.color

    depth = cv2.imread(str(IMAGE_PATH), cv2.IMREAD_ANYDEPTH)
    if depth is None:
        raise FileNotFoundError(f'Could not open {IMAGE_PATH}')

    if depth.ndim == 2:
        depth_for_display = depth.astype(np.float32)
    else:
        depth_for_display = cv2.cvtColor(depth, cv2.COLOR_BGR2GRAY).astype(np.float32)

    state = {'x': depth_for_display.shape[1] // 2, 'y': depth_for_display.shape[0] // 2}

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse, state)

    print('Keys: q=quit, c=toggle color; --color enables color mode at startup')

    while True:
        base = build_depth_display(depth_for_display, use_color, colormap)
        image = base.copy()
        x = state['x']
        y = state['y']

        if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
            image = draw_magnifier(image, x, y, depth_for_display, use_color, colormap)

        cv2.imshow(WINDOW_NAME, image)
        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            break
        if key == ord('c'):
            use_color = not use_color
            print(f'Color mode: {use_color}')

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
