"""
Crack-generation algorithm (extracted from crack_generation_gui.py).
Logic/parameters are unchanged from the original inline version.
"""

import numpy as np
import cv2

CRACK_DEPTH      = 10
PERLIN_SCALE     = 0.025
PERLIN_STRENGTH  = 1.5
THRESHOLD_LOW    = 30
THRESHOLD_HIGH   = 90
BLUR_KERNEL      = 3
EDGE_BLUR_KERNEL = 3


def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def lerp(a, b, t):
    return a + t * (b - a)


def grad(h, x, y):
    h = h & 3
    if h == 0: return  x + y
    if h == 1: return -x + y
    if h == 2: return  x - y
    return -x - y


def perlin(x, y, perm):
    xi = int(np.floor(x)) & 255
    yi = int(np.floor(y)) & 255
    xf = x - np.floor(x)
    yf = y - np.floor(y)
    u = fade(xf)
    v = fade(yf)
    aa = perm[perm[xi]     + yi]
    ab = perm[perm[xi]     + yi + 1]
    ba = perm[perm[xi + 1] + yi]
    bb = perm[perm[xi + 1] + yi + 1]
    x1 = lerp(grad(aa, xf,   yf  ), grad(ba, xf-1,   yf  ), u)
    x2 = lerp(grad(ab, xf,   yf-1), grad(bb, xf-1,   yf-1), u)
    return lerp(x1, x2, v)


def make_perm():
    p = np.arange(256, dtype=int)
    np.random.shuffle(p)
    return np.tile(p, 2)


def perlin_patch(h, w, scale=0.08, perm=None):
    if perm is None:
        perm = make_perm()
    patch = np.zeros((h, w), dtype=np.float32)
    for row in range(h):
        for col in range(w):
            patch[row, col] = perlin(col * scale, row * scale, perm)
    patch = (patch - patch.min()) / (patch.max() - patch.min() + 1e-8)
    return patch


def _build_stroke_mask_alpha(h, w, x, y, angle, length, depth):
    """Shared by draw_crack and draw_edge_stroke: builds the jittered
    stroke path, its coverage mask, a Perlin noise field over its
    bounding box, and a smooth 0-1 alpha (distance transform + sigmoid)
    restricted to the stroke. Returns (mask, alpha, noise_canvas) or
    (None, None, None) if the stroke is empty."""
    mask = np.zeros((h, w), dtype=np.uint8)
    points = []
    cur_x, cur_y, cur_angle = float(x), float(y), angle

    for i in range(int(length)):
        cur_angle += np.random.uniform(-1, 1)
        cur_x += np.cos(np.radians(cur_angle)) * np.random.uniform(0.8, 1.5)
        cur_y += np.sin(np.radians(cur_angle)) * np.random.uniform(0.8, 1.5)
        ix, iy = int(cur_x), int(cur_y)
        if 0 <= ix < w and 0 <= iy < h:
            px_width = max(1, int(depth * (1 - 0.4 * i / length)))
            cv2.circle(mask, (ix, iy), px_width, 255, -1)
            points.append((ix, iy))

    if len(points) > 2:
        cv2.polylines(mask, [np.array(points)], False, 255, 1)

    if mask.sum() == 0:
        return None, None, None

    ys, xs = np.where(mask > 0)
    x0, x1 = xs.min(), xs.max() + 1
    y0, y1 = ys.min(), ys.max() + 1
    patch_h = max(y1 - y0, 4)
    patch_w = max(x1 - x0, 4)

    perm = make_perm()
    noise_patch = perlin_patch(patch_h, patch_w, scale=PERLIN_SCALE, perm=perm)
    noise_canvas = np.zeros((h, w), dtype=np.float32)
    noise_canvas[y0:y1, x0:x1] = noise_patch

    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 3)
    dist_n = dist / (dist.max() + 1e-6)

    alpha = dist_n.copy()
    noise_smooth = cv2.GaussianBlur(noise_canvas, (5, 5), 1.2)
    noise_mod = 0.75 + 0.25 * noise_smooth
    alpha *= noise_mod

    alpha = 1.0 / (1.0 + np.exp(-10 * (alpha - 0.45)))
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.8)
    alpha = np.where(mask > 0, alpha, 0.0)
    alpha = np.clip(alpha, 0, 1)

    return mask, alpha, noise_canvas


def draw_crack(img, x, y, angle, length, depth=CRACK_DEPTH, color=0):
    """color: target shade the crack blends toward. Accepts either a
    single 0-255 grayscale value (0 = black, 255 = white) or an
    (r, g, b) tuple for a full-color crack."""
    if depth <= 0 or length < 3:
        return

    h, w = img.shape[:2]
    mask, alpha, noise_canvas = _build_stroke_mask_alpha(h, w, x, y, angle, length, depth)
    if mask is None:
        return

    img_f = img.astype(np.float32)

    variation = cv2.GaussianBlur(noise_canvas, (3, 3), 0)
    variation = 0.9 + 0.1 * variation

    strength = 1.8   # increase for deeper/darker crack
    blend_amount = np.clip(strength * alpha * variation, 0, 1)
    crack_color = img_f.copy()
    if isinstance(color, (tuple, list, np.ndarray)):
        color_target = [float(np.clip(c, 0, 255)) for c in color]
    else:
        gray = float(np.clip(color, 0, 255))
        color_target = [gray, gray, gray]
    for c in range(3):
        crack_color[:, :, c] = (
            img_f[:, :, c] * (1.0 - blend_amount) + color_target[c] * blend_amount
        )

    alpha3 = np.stack([alpha, alpha, alpha], axis=-1)
    blended = img_f * (1.0 - alpha3) + crack_color * alpha3
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    mask3 = np.stack([mask, mask, mask], axis=-1) > 0
    img[mask3] = blended[mask3]


def draw_edge_stroke(img, x, y, angle, length, depth=CRACK_DEPTH, edge_color=255):
    """Paints a strictly grayscale (black-to-white) stroke along a
    dragged path — the Edge tool. edge_color (0-255) sets how light or
    dark the mark is: 0 = solid black, 255 = solid white. Uses the same
    jittered-path/mask mechanics as draw_crack so the stroke always
    shows clearly and scales directly with edge_color, regardless of
    the underlying image content."""
    if depth <= 0 or length < 3:
        return

    h, w = img.shape[:2]
    mask, alpha, _noise_canvas = _build_stroke_mask_alpha(h, w, x, y, angle, length, depth)
    if mask is None:
        return

    img_f = img.astype(np.float32)
    gray_target = float(np.clip(edge_color, 0, 255))
    target = np.full_like(img_f, gray_target)

    alpha3 = np.stack([alpha, alpha, alpha], axis=-1)
    blended = img_f * (1.0 - alpha3) + target * alpha3
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    mask3 = np.stack([mask, mask, mask], axis=-1) > 0
    img[mask3] = blended[mask3]