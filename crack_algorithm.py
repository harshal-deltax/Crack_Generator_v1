import numpy as np
import cv2

CRACK_DEPTH     = 10     # max thickness of the crack (in pixels)
PERLIN_SCALE    = 0.025  # how "zoomed in" the noise pattern is (smaller = larger blobs)


# ==========================================================================
# PART A: PERLIN NOISE GENERATOR
# ==========================================================================

def fade(t):
    # Smoothstep-like easing curve. Makes the noise transition smoothly
    # between grid points instead of having sharp linear jumps.
    return t * t * t * (t * (t * 6 - 15) + 10)


def lerp(a, b, t):
    # Simple linear interpolation: blend between a and b by fraction t.
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
    return np.tile(p, 2)  # tiled twice to avoid index-overflow issues


def perlin_patch(h, w, scale, perm):
    
    patch = np.zeros((h, w), dtype=np.float32)
    for row in range(h):
        for col in range(w):
            patch[row, col] = perlin(col * scale, row * scale, perm)
    patch = (patch - patch.min()) / (patch.max() - patch.min() + 1e-8)
    return patch


# ==========================================================================
# PART B: THE MAIN CRACK-DRAWING FUNCTION
# ==========================================================================
def draw_crack(img, x, y, angle, length, depth=CRACK_DEPTH):
    """
    Draws one procedurally generated crack directly onto `img` (in-place).

    Parameters:
        img    : the image (numpy array, HxWx3) to draw on
        x, y   : starting pixel coordinates of the crack
        angle  : starting direction in degrees
        length : how many pixels long the crack path should be
        depth  : max thickness of the crack
    """
    if depth <= 0 or length < 3:
        return  # nothing meaningful to draw

    h, w = img.shape[:2]

    # STEP 1: Build the crack "skeleton" (the random wiggly path)
  
    crack_mask = np.zeros((h, w), dtype=np.uint8)
    points    = []
    cur_x     = float(x)
    cur_y     = float(y)
    cur_angle = angle

    for i in range(int(length)):
        # Randomly turn left/right slightly each step -> zigzag motion
        cur_angle += np.random.uniform(-1, 1)
        # Move forward in the current direction by a slightly random step size
        cur_x += np.cos(np.radians(cur_angle)) * np.random.uniform(0.8, 1.5)
        cur_y += np.sin(np.radians(cur_angle)) * np.random.uniform(0.8, 1.5)

        ix, iy = int(cur_x), int(cur_y)
        if 0 <= ix < w and 0 <= iy < h:
            
            # Width tapering
            px_width = max(1, int(depth * (1 - 0.4 * i / length)))
            cv2.circle(crack_mask, (ix, iy), px_width, 255, -1)
            points.append((ix, iy))

    if len(points) > 2:
        # Connects the dotted circle-stamps into one continuous line,
        cv2.polylines(crack_mask, [np.array(points)], False, 255, 1)

    if crack_mask.sum() == 0:
        return  # crack fell entirely outside the image bounds

    # STEP 2: Generate Perlin noise over the crack's bounding box

    ys, xs = np.where(crack_mask > 0)
    x0, x1 = xs.min(), xs.max() + 1
    y0, y1 = ys.min(), ys.max() + 1
    patch_h = max(y1 - y0, 4)
    patch_w = max(x1 - x0, 4)

    perm = make_perm()
    noise_patch = perlin_patch(patch_h, patch_w, scale=PERLIN_SCALE, perm=perm)

    # Paste the small noise patch onto a full-image
    noise_canvas = np.zeros((h, w), dtype=np.float32)
    noise_canvas[y0:y1, x0:x1] = noise_patch

    # ----------------------------------------------------------------
    # STEP 3: Distance transform (centerline = darkest, edges = faintest)
    # ----------------------------------------------------------------
    
    dist = cv2.distanceTransform(crack_mask, cv2.DIST_L2, 3)
    dist_n = dist / (dist.max() + 1e-6)   # normalize to 0-1

    alpha = dist_n.copy()   # this will become our final "darkness opacity" map

    # ----------------------------------------------------------------
    # STEP 4: Combine distance map with Perlin noise -> organic alpha
    # ----------------------------------------------------------------

    noise_smooth = cv2.GaussianBlur(noise_canvas, (5, 5), 1.2)
    noise_mod = 0.75 + 0.25 * noise_smooth   # keep noise effect subtle (75%-100% range)
    alpha *= noise_mod

    alpha = 1.0 / (1.0 + np.exp(-10 * (alpha - 0.45)))

    # Light blur so the alpha mask doesn't have jagged/aliased pixel edges.
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.8)

    # Zero-out anything outside the original crack path (safety clamp).
    alpha = np.where(crack_mask > 0, alpha, 0.0)
    alpha = np.clip(alpha, 0, 1)

    # ----------------------------------------------------------------
    # STEP 5: Apply darkening to the image using alpha as a blend mask
    # ----------------------------------------------------------------

    img_f = img.astype(np.float32)

    variation = cv2.GaussianBlur(noise_canvas, (3, 3), 0)
    variation = 0.9 + 0.1 * variation

    strength = 1.8  # how dark the crack's center can get; higher = deeper-looking
    crack_color = img_f.copy()
    for c in range(3):  # apply identically to R, G, B channels
        crack_color[:, :, c] = img_f[:, :, c] * (1.0 - strength * alpha * variation)

    # Safety: never allow the result to be brighter than the original pixel
    crack_color = np.minimum(crack_color, img_f)

    # Final blend: alpha=0 -> keep original pixel, alpha=1 -> fully use
    # the darkened crack_color. Values in between mix proportionally.
    alpha3 = np.stack([alpha, alpha, alpha], axis=-1)
    blended = img_f * (1.0 - alpha3) + crack_color * alpha3
    blended = np.minimum(blended, img_f)
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    # Write the blended pixels back into the original image, but ONLY
    mask3 = np.stack([crack_mask, crack_mask, crack_mask], axis=-1) > 0
    img[mask3] = blended[mask3]



def draw_center_crack(img, x, y, angle, length, depth=CRACK_DEPTH):
    if depth <= 0 or length < 3:
        return

    h, w = img.shape[:2]

    # 1. Build crack skeleton
    crack_mask = np.zeros((h, w), dtype=np.uint8)
    points    = []
    cur_x     = float(x)
    cur_y     = float(y)
    cur_angle = angle

    for i in range(int(length)):
        cur_angle += np.random.uniform(-1, 1)
        cur_x     += np.cos(np.radians(cur_angle)) * np.random.uniform(0.8, 1.5)
        cur_y     += np.sin(np.radians(cur_angle)) * np.random.uniform(0.8, 1.5)
        ix, iy = int(cur_x), int(cur_y)
        if 0 <= ix < w and 0 <= iy < h:
            half = length / 2

            if i <= half:
                # Increase width
                px_width = max(1, int(depth * (1 +  0.4 * i / half)))
            else:
                # Decrease width
                px_width = max(1, int(depth * (1 + 0.4 * (1 - (i - half) / half))))

            cv2.circle(crack_mask, (ix, iy), px_width, 255, -1)
            points.append((ix, iy))

    if len(points) > 2:
        cv2.polylines(crack_mask, [np.array(points)], False, 255, 1)

    if crack_mask.sum() == 0:
        return

    # 2. Perlin noise
    ys, xs = np.where(crack_mask > 0)
    x0, x1 = xs.min(), xs.max() + 1
    y0, y1 = ys.min(), ys.max() + 1
    patch_h = max(y1 - y0, 4)
    patch_w = max(x1 - x0, 4)

    perm        = make_perm()
    noise_patch = perlin_patch(
        patch_h,
         patch_w,
            scale=PERLIN_SCALE,
            perm=perm)
    noise_canvas = np.zeros((h, w), dtype=np.float32)
    noise_canvas[y0:y1, x0:x1] = noise_patch
    # 3. Distance transform
    dist = cv2.distanceTransform(crack_mask, cv2.DIST_L2, 3)
    dist_n = dist / (dist.max() + 1e-6)

    # Start with normalized distance
    alpha = dist_n.copy()

    # Smooth Perlin noise
    noise_smooth = cv2.GaussianBlur(noise_canvas, (5,5), 1.2)
    #noise_mod = 0.75 + 0.25 * noise_smooth
    noise_mod = 0.75 + 0.25 * noise_smooth
    # Apply Perlin texture
    alpha *= noise_mod

    # Nonlinear threshold (sigmoid)
    alpha = 1.0 / (1.0 + np.exp(-10 * (alpha - 0.45)))

    # Smooth crack edge
    alpha = cv2.GaussianBlur(alpha, (3,3), 0.8)

    # Restrict to crack region
    alpha = np.where(crack_mask > 0, alpha, 0.0)
    alpha = np.clip(alpha, 0, 1)
    # 4. Crack colour — pure darkening, strength controls how black the centre is
    img_f = img.astype(np.float32)

    variation = cv2.GaussianBlur(noise_canvas, (3, 3), 0)
    variation  = 0.9 + 0.1 * variation

    strength    = 1.8   # increase for deeper/darker crack
    crack_color = img_f.copy()
    for c in range(3):
        crack_color[:, :, c] = img_f[:, :, c] * (1.0 - strength * alpha * variation)

    # Absolute clamp — never brighter than original
    crack_color = np.minimum(crack_color, img_f)

    # 5. Blend and write back strictly inside crack_mask
    alpha3  = np.stack([alpha, alpha, alpha], axis=-1)
    blended = img_f * (1.0 - alpha3) + crack_color * alpha3
    blended = np.minimum(blended, img_f)
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    mask3 = np.stack([crack_mask, crack_mask, crack_mask], axis=-1) > 0
    img[mask3] = blended[mask3]
