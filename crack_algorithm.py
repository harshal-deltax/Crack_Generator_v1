import cv2
import numpy as np
from tkinter import Tk
from tkinter.filedialog import askopenfilename

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

# -------------------------------------------------------
# Select Image
# -------------------------------------------------------
root = Tk()
root.withdraw()

filename = askopenfilename(
    title="Select Metal Image",
    filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
)

if filename == "":
    print("No image selected.")
    exit()

image = cv2.imread(filename)

if image is None:
    print("Could not open image.")
    exit()

original = image.copy()

# -------------------------------------------------------
# Parameters
# -------------------------------------------------------
CRACK_DEPTH      = 10
PERLIN_SCALE     = 0.025
PERLIN_STRENGTH  = 1.5
THRESHOLD_LOW    = 30
THRESHOLD_HIGH   = 90
BLUR_KERNEL      = 3
EDGE_BLUR_KERNEL = 3

# -------------------------------------------------------
# Core
def draw_crack(img, x, y, angle, length, depth=CRACK_DEPTH):
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
        cur_angle += np.random.uniform(-5, 5)
        cur_x     += np.cos(np.radians(cur_angle)) * np.random.uniform(0.8, 1.5)
        cur_y     += np.sin(np.radians(cur_angle)) * np.random.uniform(0.8, 1.5)
        ix, iy = int(cur_x), int(cur_y)
        if 0 <= ix < w and 0 <= iy < h:
            px_width = max(1, int(depth * (1 - i / length)))
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
# -------------------------------------------------------
# Mouse callback
# -------------------------------------------------------
drawing = False
start_x = 0
start_y = 0

def mouse(event, x, y, flags, param):
    global drawing, start_x, start_y, image

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_x = x
        start_y = y

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        temp = image.copy()
        cv2.circle(temp, (start_x, start_y), 4, (0, 0, 255), -1)
        cv2.line(temp, (start_x, start_y), (x, y), (0, 255, 0), 2)
        cv2.imshow("Synthetic Crack", temp)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        dx     = x - start_x
        dy     = y - start_y
        length = np.sqrt(dx*dx + dy*dy)
        angle  = np.degrees(np.arctan2(dy, dx))
        draw_crack(image, start_x, start_y, angle, length, depth=CRACK_DEPTH)
        cv2.imshow("Synthetic Crack", image)


# -------------------------------------------------------
# Window + main loop
# -------------------------------------------------------
cv2.namedWindow("Synthetic Crack")
cv2.setMouseCallback("Synthetic Crack", mouse)

print("\nControls")
print("----------------------")
print("Left Click + Drag : Draw crack")
print("R                 : Reset")
print("S                 : Save  →  synthetic_crack_enhanced.png")
print("Q                 : Quit\n")

while True:
    cv2.imshow("Synthetic Crack", image)
    key = cv2.waitKey(20) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        image = original.copy()
        print("Reset.")
    elif key == ord('s'):
        cv2.imwrite("synthetic_crack_enhanced.png", image)
        print("Saved: synthetic_crack_enhanced.png")

cv2.destroyAllWindows()