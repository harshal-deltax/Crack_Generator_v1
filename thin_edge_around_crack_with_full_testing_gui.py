import os
import io
import base64
import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageTk


# --------------------------------------------------------------------------
# Simple dark theme palette
# --------------------------------------------------------------------------
BG_DARK = "#1e1e1e"
BG_PANEL = "#252526"
BG_CANVAS = "#3a3a3a"
ACCENT = "#0e7afe"
BTN_BG = "#3c3c3c"
BTN_BG_HOVER = "#4a4a4a"
TEXT_LIGHT = "#e8e8e8"
TEXT_DIM = "#9a9a9a"

ICON_SIZE = (28, 28)
# user's brush-pen photo rather than embedding the photo itself).
BRUSH_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAADeElEQVR4nMWWW2gcVRjH/2fO2e5MLk3c7G5xM+5OZ9bdJrF2JW5rIrhYsTR0W2lhvRShVaRIFRSLKCgsPogo+CCIbwapQpuKleJDHvpQxjyVVktJainEdqO5bIKXdbvZJDNn9viwYxKVFtdM6P9pYC6/c+b7nXM+4A6FAKBAjgKQ7sQA6Hp+nCQSiWA0anxqGMmvwmF1KwBkMhm2bsRYzPhA1xOiu/t+0dvb90ckEs2ughIvWX/Va4EQgkqlMruwUPV3dqrfxOPJV0zT5Pl8nsDDuhIAUjweb7FtHGeMPmFZ1rwsywgEgs3l8u+fXL069jIAgXpdHS+AxP0gNC3+oSTR1xzHrlLK7FAo3DY/Xx0eG/v+IIASkGGAydcClFwYASAVCuPHHMc5KklMcRxHLhZnfpNl/0AqlR5pbW1NAiZfq0zkH9cUANe0+C5CyEkAd3HOfwkEOoKM+X6dnp58Zmbm57OZTIaZpum4g11r6jOIxWJdmnbvmK4nhKpqpZ6ebSKd7ue6Hn8RAPL5vIT/YfCtXmAAuKqqAcbkLyilA3WZlA2BQIevVCq9f+3a6JvusxKA2lqBwIqVRNOMjyllR23brjDGSCgUbq5W578eHb10CMDNRmS63fpy3PukUPjxJc75MUqpXKvVaLE4XZZlZX8qlTb9/ja9EZn+Sw1WyWTsA6TjhKCNc14JBkMtkiQVp6YmnyoWJ791ZbrtTBsoev23aZq2jRA2RAhNWtbSzfb29iZFaa7Nzc0cmZi4/ln9xPmyhlsY3KhlDADftEkPK4p0klL6qGVZZVlWmkKhEKNUendk5NzbhBAIIZY3lNVpdI/kAOjs7PW5QmF8l+PwQZ/Pt9GylhZt217cvv2htwYHPz8hhGhxgZ5t/MtrMBrV3tix42Fx+PALzpkzw4v9fY+ISCR6GgAy8PaII7lcjgLAzp2P54aGTld2794r2gLhsmEkFz7qeuwBADhV7yI8DQOAbHZ/Wu2M/hDZbCy9urlP/NTz7NTEg8/pAHAq5z2UAkC2N9vUp265b/iegRMXjQPiStfT46L/+VYAEMh72yu5e+tyhrU9+84bB25c3vLkhYu9R3x1KIin7QPc8zUP4B2gdi52SO6Qq+/5Kd3Qomx8PfLd3Yse81ayWpYb3QdTl5O5rcLj/uhfEQARf7d0fYErYI+FaSR/AtCQL5EjxoEYAAAAAElFTkSuQmCC"

# Eraser icon: an original flat-style icon (drawn here, not the watermarked
# stock preview image), designed to visually pair with the brush icon above.
ERASER_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAEv0lEQVR4nM2WXWwUVRTH/+fe2Y/a7ZbPoqRCQTDIRxBKIipxUywtoZqoZKsJlgcejBBNSDACwWTSJ0p48ImHGo0aTAgdDOFFCA1uKhrahEYDTSVYLS3QbUvbaXe33Z2duff40FYLLS0gJP6TeTz3d87/nHvuAP8HsWkKNk1BADgalSZM8eRg9zm8LhqVjx9mjsIulrxV3FlRdbLrjaqmzoqq2rOR8iIA4EjE+K8Mmgij6mp94dWKtWtmz/s53+8PjSgPudIHO+vEb6UTu4ovnD7HpilQXc0E8CMDGSAw44sNW8IVC55uDPsDK1JuNgvAYEDnSMPQYO7LpA+uOH/yCDBqcaVlqYcFCgAE0yQi4tfnF3w1L5izIullPSLyE5EQREZaedrVGotD4ZqObTtO1BQX51daloo9gsXE0agky1KtZe8eWBoKHx7IZjwCTTqIRy1Uc/wBw846V68lh3aWNJz5jaN1kqxKjQe0WJBlqTMvbV4Q9vkPDXuuBjDlNBJABBj9TsbLNXxrVuXN+ulKWeUOsioVM8M0H+zqGABQkDO7KCBkKKMUCyKaLkAQGSnXVT4p8pbkhL5rLnl7HRHtB6CYWRLRtH0VANDlJNod5SWDUoIZMw4CEaQSxLe7e9SyD6v2DY0Mnvv++PFCIlLMPG1fBUejcvul+t5B1zkYEJJ8Qkg9A1T4DKT7bMKWV6Rve6kXDvpLy98s++Xqr40lROQxs2TmKZ0SZFmKTVOsrreOXR9ORBlsh30+qZm9KauTEm4ihVTRQhTu2wWMZIyUbaucYGDRsuXLz3e0te4lIkVEzMyT+ioAgKqrNUejcn29deqKbW9KednmuYGgwQzFE6ePCHA92JKw8NBuyGAA2vUgDEOOjIxoVp5c9NySz3vj7d+ae/aEiEjHYrG7LL6r7FgkYpQ0NHh7Vq4MfVq07lhBIGdnws2yYmZBJKSU6LvTj/BnuzG/fBNcOwEy/h1qZmYAOnfWHJm07ebWlpadG18rbZ04TJN8Hl9xANBaVrm3IPjUUUFkZAGV7O2T9N42PPtxFVx7CCSn3udaay8UDhvpdNq+1XHzg+dXrz81mjPpKRvLACEaFWRZ6vLmd0oW5+V/Y6TSi26/sNhbenS/wRln1N5ppLVWfr9f+oI56Gxv/6ho+epjzCynjeJIxKCGBu+HyNbCwoLCr9d8ebg04xPKS2eEkNPHAgAzq0AgINLpdOrS5cZl5eXbe2cOGlt9YJY93R1H5s+ds8/NZuFmXUWCZnwjtdbs9/up7dofG1dteLlpxnVElqVM0xRMpBc8U/RJ+5833leMZG5eSGqtp7w6E2GBYJAdx0m13W6/MRNrEpuZJQA0xWIvJuz4FWaHU3bcTdlxPTzYzfd+KTvuMjvccb3lAACMxz+Uxu9VbU1Nfl9PxwnmDA8PduvkQJeaCEsOdLnMDnd3tp0ag40+hY+iurq6fzK9+de1/elUv3bTNicHutyUHVfJgbij3SQP9t36vba2Np+Z6X6r7oE1dogAgJbmpq3DQz1dzC5rZ4iZszycuJO8eOHc2gnVPR6Nvw6xs6eL7sQ7aof6u5r6ejpPNjf+WPzYYeOaaPE9yTy5/1nTNMXYzgQziycKexj9Da9PoY8wpvZRAAAAAElFTkSuQmCC"
# ==========================================================================
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


def draw_crack(
    img, x, y, angle, length, depth=CRACK_DEPTH,
    # ---- Reflection/rim controls ----
    reflect_rim_inner=0.38,    # how close to the dark core the glint starts (0-1, LOCAL, same scale as the core's own darkening threshold ~0.45 - keep this just BELOW that to guarantee overlap/no gap)
    reflect_rim_outer=0.55,    # how far out the glint extends (0-1, LOCAL). Keep close to reflect_rim_inner for a thin band; both now scale with the crack's *local* thickness at each point, matching the core.
    reflect_max_alpha=0.35,    # max opacity/transparency of the glint (0=invisible, 1=fully opaque)
    reflect_lighten=255.0,      # brightness (no color) OR mix strength toward reflect_color (0-255, acts like 0-100%)
    reflect_blur_sigma=0.6,    # softness of the glint edge (higher = softer/more spread, may reopen gap)
    reflect_noise_floor=0.25,  # patchiness threshold (0-1, higher = sparser/more broken-up glint)
    reflect_color= (200,200,200),        # NEW: e.g. (180, 220, 255) for icy blue, (255, 200, 120) for gold. None = old lighten behavior
):
    if depth <= 0 or length < 3:
        return

    h, w = img.shape[:2]

    # 1. Build crack skeleton
    crack_mask = np.zeros((h, w), dtype=np.uint8)
    points    = []
    widths    = []   # local half-width (px) at each skeleton point, used later
                      # to make the rim/reflection scale with local crack width
                      # instead of the crack's single widest point.
    cur_x     = float(x)
    cur_y     = float(y)
    cur_angle = angle

    for i in range(int(length)):
        cur_angle += np.random.uniform(-1, 1)
        cur_x     += np.cos(np.radians(cur_angle)) * np.random.uniform(0.8, 1.5)
        cur_y     += np.sin(np.radians(cur_angle)) * np.random.uniform(0.8, 1.5)
        ix, iy = int(cur_x), int(cur_y)
        if 0 <= ix < w and 0 <= iy < h:
            px_width = max(1, int(depth * (1 - i * 0.40 / length)))
            cv2.circle(crack_mask, (ix, iy), px_width, 255, -1)
            points.append((ix, iy))
            widths.append(px_width)

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
    
    width_map = np.zeros((h, w), dtype=np.float32)
    for (px, py), pw in zip(points, widths):
        y0p, y1p = max(0, py - pw), min(h, py + pw + 1)
        x0p, x1p = max(0, px - pw), min(w, px + pw + 1)
        if y1p <= y0p or x1p <= x0p:
            continue
        yy, xx = np.ogrid[y0p:y1p, x0p:x1p]
        circle = (xx - px) ** 2 + (yy - py) ** 2 <= pw * pw
        sub = width_map[y0p:y1p, x0p:x1p]
        sub[circle] = np.maximum(sub[circle], pw)

    dist_n_rim = np.clip(dist / (width_map + 1e-6), 0.0, 1.0)

    # Start with normalized LOCAL distance (was global dist_n before - that's
    # what made the core's width ignore local thickness).
    alpha = dist_n_rim.copy()

    # Smooth Perlin noise
    noise_smooth = cv2.GaussianBlur(noise_canvas, (5, 5), 1.2)
    noise_mod = 0.75 + 0.25 * noise_smooth
    # Apply Perlin texture
    alpha *= noise_mod

    # Nonlinear threshold (sigmoid) - high steepness gives a sharp,
    # near-binary cutoff between crack and surface.
    SIGMOID_STEEPNESS = 10.0
    SIGMOID_CENTER = 0.52
    alpha = 1.0 / (1.0 + np.exp(-SIGMOID_STEEPNESS * (alpha - SIGMOID_CENTER)))

    # Minimal smoothing - just enough to avoid raw jagged pixels, while
    # keeping the crack edge crisp instead of feathered.
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.4)

    # Restrict to crack 
    #########################################
    alpha[alpha < 0.08] = 0.0
    #########################################
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
    blended = np.clip(blended, 0, 255)

    # ---- Reflection / specular highlight on the crack lips ---------------
    # Same local dist_n_rim scale as the core above, so the rim's inner
    # bound (reflect_rim_inner) can simply be placed just inside the core's
    # own SIGMOID_CENTER threshold to guarantee overlap (no gap) - and both
    # the core and the rim shrink together on thin sections instead of one
    # being global and the other local.
    rim_mask = np.where(
        (crack_mask > 0)
        & (dist_n_rim >= reflect_rim_inner)
        & (dist_n_rim <= reflect_rim_outer),
        1.0, 0.0
    ).astype(np.float32)

    # Perlin noise on the rim → patchy, intermittent glint
    rim_noise      = cv2.GaussianBlur(noise_canvas, (3, 3), 0.6)
    rim_noise_norm = (rim_noise - rim_noise.min()) / (rim_noise.max() - rim_noise.min() + 1e-8)

    #uniformity
    #################################################################
    rim_glint      = int(1) # np.clip((rim_noise_norm - reflect_noise_floor) / (1.0 - reflect_noise_floor + 1e-8), 0.0, 1.0)
    #########################################

    # Directional light gradient (light from top-left, angle 45°)
    yy, xx    = np.mgrid[0:h, 0:w].astype(np.float32)
    light_ang = np.radians(45.0)
    grad_raw  = xx * np.cos(light_ang) + yy * np.sin(light_ang)
    grad_raw  = (grad_raw - grad_raw.min()) / (grad_raw.max() - grad_raw.min() + 1e-8)
    light_dir = 0.15 + 0.85 * grad_raw   # floor lowered so unlit side isn't half-lit

    reflect_alpha = rim_mask * rim_glint * light_dir
    reflect_alpha = cv2.GaussianBlur(reflect_alpha, (3, 3), reflect_blur_sigma)
    reflect_alpha = np.clip(reflect_alpha, 0.0, reflect_max_alpha)

    # Blend toward either a flat tint color (reflect_color) or a lightened
    # version of the pixel's own color, so it reads as a glint/sheen rather
    # than painted-on white.
    if reflect_color is not None:
        color_arr = np.array(reflect_color, dtype=np.float32).reshape(1, 1, 3)
        mix = np.clip(reflect_lighten / 255.0, 0.0, 1.0)
        highlight_target = np.clip(blended * (1 - mix) + color_arr * mix, 0, 255)
    else:
        highlight_target = np.clip(blended + reflect_lighten, 0, 255)

    reflect_alpha3 = np.stack([reflect_alpha, reflect_alpha, reflect_alpha], axis=-1)
    blended = blended * (1.0 - reflect_alpha3) + highlight_target * reflect_alpha3
    blended = np.clip(blended, 0, 255)
    # -------------------------------------------------------------------

    blended = blended.astype(np.uint8)
    mask3 = np.stack([crack_mask, crack_mask, crack_mask], axis=-1) > 0
    img[mask3] = blended[mask3]
class RoundedButton(tk.Canvas):
   
    def __init__(self, parent, image, command, bg_parent, base_bg, hover_bg,
                 active_bg, width=104, height=44, radius=14, border_color="#5a5a5a",
                 text=None, text_angle=0, font=("Segoe UI", 16, "bold"), fg=TEXT_LIGHT,
                 active_border_color=None):
        super().__init__(parent, width=width, height=height, bg=bg_parent,
                          highlightthickness=0, cursor="hand2")
        self.command = command
        self.image_ref = image
        self.text = text
        self.text_angle = text_angle
        self.font = font
        self.fg = fg
        self.base_bg = base_bg
        self.hover_bg = hover_bg
        self.active_bg = active_bg
        self.border_color = border_color
        self.active_border_color = active_border_color or border_color
        self._active = False
        self._disabled = False
        self._btn_w = width
        self._btn_h = height
        self._radius = radius

        self._draw(base_bg)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", self._on_resize)

    def _rounded_points(self, x0, y0, x1, y1, r):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        return [
            x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r,
            x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1,
            x0, y1, x0, y1 - r, x0, y0 + r, x0, y0,
        ]

    def _draw(self, color):
        self.delete("all")
        pad = 2
        fill_color = "#2a2a2a" if self._disabled else color
        outline_color = self.active_border_color if (self._active and not self._disabled) else self.border_color
        outline_width = 2 if (self._active and not self._disabled) else 1
        pts = self._rounded_points(pad, pad, self._btn_w - pad, self._btn_h - pad, self._radius)
        self.create_polygon(pts, smooth=True, fill=fill_color, outline=outline_color, width=outline_width)
        cx, cy = self._btn_w // 2, self._btn_h // 2
        if self.image_ref is not None:
            self.create_image(cx, cy, image=self.image_ref)
        elif self.text:
            text_fg = "#5a5a5a" if self._disabled else self.fg
            self.create_text(cx, cy, text=self.text, fill=text_fg, font=self.font, angle=self.text_angle)

    def _on_enter(self, _event=None):
        if self._disabled:
            return
        self._draw(self.hover_bg)

    def _on_leave(self, _event=None):
        self._draw(self.active_bg if self._active else self.base_bg)

    def _on_click(self, _event=None):
        if self._disabled:
            return
        if self.command:
            self.command()

    def _on_resize(self, event):
        self._btn_w, self._btn_h = event.width, event.height
        self._draw(self.active_bg if self._active else self.base_bg)

    def set_active(self, active):
        self._active = active
        self._draw(self.active_bg if active else self.base_bg)

    def config(self, **kwargs):
        if "state" in kwargs:
            state = kwargs.pop("state")
            self._disabled = (state == "disabled")
            self._draw(self.active_bg if self._active else self.base_bg)
        if kwargs:
            super().config(**kwargs)

    configure = config

    def cget(self, key):
        if key == "state":
            return "disabled" if self._disabled else "normal"
        return super().cget(key)

    def __getitem__(self, key):
        return self.cget(key)


class ImagePainterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CrackGeneratorGUI")
        self.root.geometry("1180x740")
        self.root.minsize(880, 560)
        self.root.configure(bg=BG_DARK)

        # ---- image / drawing state ----
        self.original_image = None     # PIL.Image, untouched upload
        self.image = None              # PIL.Image, current working copy
        self.tk_image = None           # ImageTk.PhotoImage on screen
        self.image_path = None

        self.zoom = 1.0
        self.tool = "brush"            # "brush" | "erase"
        self.brush_size = 1.0          # fractional sizes supported (min 0.25, step 0.25)
        self.brush_color = (30, 28, 26)  # near-black by default

        self.undo_stack = []
        self.redo_stack = []
        self.max_undo = 40
        self.last_point = None
        self.placeholder_id = None
        self._zoom_sync_lock = False
        self._img_offset = (0, 0)
        self._crack_start_img = None
        self._crack_start_canvas = None
        self._crack_preview_ids = []

        self._build_ui()

    # ----------------------------------------------------------------
    # UI construction
    # ----------------------------------------------------------------
    def _build_ui(self):
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(fill="both", expand=True)
        self._build_toolbar(main)
        self._build_canvas(main)

    def _build_canvas(self, parent):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.pack(side="left", fill="both", expand=True)

        holder = tk.Frame(frame, bg=BG_DARK)
        holder.pack(fill="both", expand=True, padx=(10, 0), pady=10)

        v_scroll = tk.Scrollbar(holder, orient="vertical")
        h_scroll = tk.Scrollbar(holder, orient="horizontal")

        self.canvas = tk.Canvas(
            holder, bg=BG_CANVAS, highlightthickness=0, cursor="cross",
            xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set,
        )
        v_scroll.config(command=self.canvas.yview)
        h_scroll.config(command=self.canvas.xview)

        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.placeholder_id = self.canvas.create_text(
            400, 280,
            text="Upload an image to start drawing",
            fill=TEXT_DIM, font=("Segoe UI", 14),
        )

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Control-MouseWheel>", self._on_wheel_zoom)        # Win/macOS
        self.canvas.bind("<Control-Button-4>", lambda e: self.zoom_in())    # Linux scroll up
        self.canvas.bind("<Control-Button-5>", lambda e: self.zoom_out())   # Linux scroll down
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        self.status_label = tk.Label(
            frame, text="No image loaded", anchor="w",
            bg=BG_DARK, fg=TEXT_DIM, font=("Segoe UI", 9),
        )
        self.status_label.pack(fill="x", padx=12, pady=(0, 8))

        # ---- floating zoom control, bottom-left of the canvas ----
        self.zoom_overlay = tk.Frame(
            holder, bg=BG_PANEL, highlightbackground="#555555", highlightthickness=1
        )
        self.zoom_overlay.place(relx=0.0, rely=1.0, anchor="sw", x=10, y=-28)

        zo_out_btn = self._make_button(self.zoom_overlay, "-", self.zoom_out, width=3)
        zo_out_btn.pack(side="left", padx=(6, 4), pady=6)

        self.zoom_slider = tk.Scale(
            self.zoom_overlay, from_=5, to=400, resolution=5, orient="horizontal", length=130,
            bg=BG_PANEL, fg=TEXT_LIGHT, troughcolor=BTN_BG, highlightthickness=0,
            activebackground=ACCENT, showvalue=False, command=self._on_zoom_slider,
        )
        self.zoom_slider.set(int(self.zoom * 100))
        self.zoom_slider.pack(side="left", padx=4, pady=6)
        self.zoom_slider.bind("<ButtonRelease-1>", lambda e: self.redraw_canvas(fast=False))

        zo_in_btn = self._make_button(self.zoom_overlay, "+", self.zoom_in, width=3)
        zo_in_btn.pack(side="left", padx=(4, 6), pady=6)

        self.zoom_label = tk.Label(self.zoom_overlay, text="100%", bg=BG_PANEL, fg=TEXT_LIGHT,
                                    font=("Segoe UI", 9, "bold"), width=4)
        self.zoom_label.pack(side="left", padx=(0, 8), pady=6)

    def _build_toolbar(self, parent):
        panel = tk.Frame(parent, bg=BG_PANEL, width=240)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        # ---- Download Image: pinned to the very bottom of the panel ----
        bottom = tk.Frame(panel, bg=BG_PANEL)
        bottom.pack(side="bottom", fill="x", padx=16, pady=(16, 32))
        tk.Frame(bottom, bg="#3a3a3a", height=1).pack(fill="x", pady=(0, 12))
        self.download_btn = self._make_button(bottom, "\u2b07  Download Image", self.download_image)
        self.download_btn.pack(fill="x")

        # ---- everything else flows from the top, filling the rest ----
        top = tk.Frame(panel, bg=BG_PANEL)
        top.pack(side="top", fill="both", expand=True)

        def section_title(text):
            tk.Label(top, text=text, bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(18, 4))

        def separator():
            tk.Frame(top, bg="#3a3a3a", height=1).pack(fill="x", padx=16, pady=10)

        tk.Label(top, text="CrackGeneratorGUI", bg=BG_PANEL, fg=TEXT_LIGHT,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=16, pady=(18, 0))

        # ---- File: top only has Upload ----
        section_title("FILE")
        self.upload_btn = self._make_button(top, "\u2b06  Upload Image", self.upload_image)
        self.upload_btn.pack(fill="x", padx=16, pady=4)

        separator()

        # ---- Tools ----
        section_title("TOOLS")
        self.brush_icon_img = self._load_icon(BRUSH_ICON_B64)
        self.erase_icon_img = self._load_icon(ERASER_ICON_B64)

        tools_row = tk.Frame(top, bg=BG_PANEL)
        tools_row.pack(fill="x", padx=16, pady=4)

        self.brush_btn = RoundedButton(
            tools_row, self.brush_icon_img, lambda: self.select_tool("brush"),
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=ACCENT,
        )
        self.brush_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.erase_btn = RoundedButton(
            tools_row, self.erase_icon_img, lambda: self.select_tool("erase"),
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=ACCENT,
        )
        self.erase_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

        self._caption_row(top, ["Brush", "Erase"])

        size_row = tk.Frame(top, bg=BG_PANEL)
        size_row.pack(fill="x", padx=16, pady=(12, 0))
        tk.Label(size_row, text="Brush Size", bg=BG_PANEL, fg=TEXT_LIGHT,
                 font=("Segoe UI", 9)).pack(side="left")
        self.size_value_label = tk.Label(
            size_row, text=f"{self.brush_size:.2f}", bg=BG_PANEL, fg=TEXT_DIM, font=("Segoe UI", 9)
        )
        self.size_value_label.pack(side="right")

        self.size_scale = tk.Scale(
            top, from_=0.25, to=20, resolution=0.25, digits=4, orient="horizontal",
            bg=BG_PANEL, fg=TEXT_LIGHT, troughcolor=BTN_BG, highlightthickness=0,
            activebackground=ACCENT, showvalue=False, command=self._on_size_change,
        )
        self.size_scale.set(self.brush_size)
        self.size_scale.pack(fill="x", padx=16, pady=(0, 4))

        color_row = tk.Frame(top, bg=BG_PANEL)
        color_row.pack(fill="x", padx=16, pady=(8, 4))
        tk.Label(color_row, text="Brush Color", bg=BG_PANEL, fg=TEXT_LIGHT,
                 font=("Segoe UI", 9)).pack(side="left")
        self.color_swatch = tk.Label(
            color_row, bg=self._rgb_to_hex(self.brush_color), width=4, height=1,
            relief="ridge", cursor="hand2",
        )
        self.color_swatch.pack(side="right")
        self.color_swatch.bind("<Button-1>", lambda e: self.pick_color())

        self._update_tool_buttons()

        separator()

        # ---- History: Undo / Redo / Reset, as icon buttons ----
        section_title("HISTORY")
        history_row = tk.Frame(top, bg=BG_PANEL)
        history_row.pack(fill="x", padx=16, pady=4)

        self.undo_btn = RoundedButton(
            history_row, None, self.undo,
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=BTN_BG,
            width=60, height=44, radius=0, text="\u21BA", text_angle=90,
        )
        self.undo_btn.pack(side="left", expand=True, fill="x", padx=(0, 3))
        self.redo_btn = RoundedButton(
            history_row, None, self.redo,
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=BTN_BG,
            width=60, height=44, radius=0, text="\u21BB", text_angle=-90,
        )
        self.redo_btn.pack(side="left", expand=True, fill="x", padx=3)
        self.reset_btn = self._make_button(history_row, "\U0001F5D1", self.reset_image, width=3,
                                            base_bg="#c9c9c9", hover_bg="#dadada", fg="#222222")
        self.reset_btn.config(highlightthickness=3, highlightbackground="#e53935",
                               highlightcolor="#e53935")
        self.reset_btn.pack(side="left", expand=True, fill="x", padx=(3, 0))

        self.undo_btn.config(state="disabled")
        self.redo_btn.config(state="disabled")

        self._caption_row(top, ["Undo", "Redo", "Reset"])

        separator()

        # ---- Effects: convert the image to black & white ----
        section_title("EFFECTS")
        self.bw_btn = self._make_button(top, "\u25D1  Convert to B&W", self.convert_to_bw)
        self.bw_btn.pack(fill="x", padx=16, pady=4)

        separator()

        tk.Label(
            top, text="Tip: click & drag on the image\nto draw or erase. Ctrl + scroll,\nor the slider below, also zooms.",
            bg=BG_PANEL, fg=TEXT_DIM, font=("Segoe UI", 8), justify="left",
        ).pack(anchor="w", padx=16, pady=(22, 10))

    def _make_button(self, parent, text, command, width=None, image=None, danger=False,
                      base_bg=None, hover_bg=None, fg=None):
        if base_bg is None:
            base_bg = "#7a2020" if danger else BTN_BG
        if hover_bg is None:
            hover_bg = "#9c2b2b" if danger else BTN_BG_HOVER
        fg = fg or TEXT_LIGHT
        kwargs = dict(
            command=command, bg=base_bg, fg=fg,
            activebackground=hover_bg, activeforeground=fg,
            relief="flat", bd=0, font=("Segoe UI", 10), cursor="hand2",
            padx=8, pady=8, width=width,
        )
        if image is not None:
            kwargs["image"] = image
            if text:
                kwargs["text"] = text
                kwargs["compound"] = "left"
        else:
            kwargs["text"] = text
        btn = tk.Button(parent, **kwargs)
        if image is not None:
            btn.image = image  # keep a reference so Tk doesn't garbage-collect it
        btn._active = False
        btn._base_bg = base_bg
        btn._hover_bg = hover_bg
        btn.bind("<Enter>", lambda e: btn.config(bg=btn._hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=ACCENT if btn._active else btn._base_bg))
        return btn

    @staticmethod
    def _load_icon(b64_data, size=ICON_SIZE):
        """Decode a base64-embedded PNG into a Tk-displayable icon."""
        raw = base64.b64decode(b64_data)
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        if img.size != size:
            img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def _caption_row(self, parent, labels):
        """A row of evenly-spaced captions under a row of equal-width buttons,
        so each label lines up under its button (used for Brush/Erase and
        Undo/Redo/Reset). Returns the created Label widgets."""
        row = tk.Frame(parent, bg=BG_PANEL)
        row.pack(fill="x", padx=16, pady=(0, 4))
        created = []
        for label in labels:
            lbl = tk.Label(row, text=label, bg=BG_PANEL, fg=TEXT_DIM, font=("Segoe UI", 8))
            lbl.pack(side="left", expand=True)
            created.append(lbl)
        return created

    # ----------------------------------------------------------------
    # Small helpers
    # ----------------------------------------------------------------
    @staticmethod
    def _rgb_to_hex(rgb):
        return "#%02x%02x%02x" % rgb

    def _update_tool_buttons(self):
        for btn, tool in ((self.brush_btn, "brush"), (self.erase_btn, "erase")):
            btn.set_active(self.tool == tool)

    def _update_status(self):
        if self.image is None:
            self.status_label.config(text="No image loaded")
            return
        w, h = self.image.size
        name = os.path.basename(self.image_path) if self.image_path else "untitled"
        tool = "Brush" if self.tool == "brush" else "Erase"
        self.status_label.config(
            text=f"{name}   |   {w}x{h}px   |   zoom {int(self.zoom * 100)}%   |   tool: {tool}"
        )

    def select_tool(self, tool):
        self.tool = tool
        self._update_tool_buttons()
        self._update_status()

    def _on_size_change(self, value):
        self.brush_size = max(0.25, float(value))
        if hasattr(self, "size_value_label"):
            self.size_value_label.config(text=f"{self.brush_size:.2f}")

    def pick_color(self):
        rgb, hex_color = colorchooser.askcolor(
            color=self._rgb_to_hex(self.brush_color), title="Choose brush color"
        )
        if rgb:
            self.brush_color = tuple(int(c) for c in rgb)
            self.color_swatch.config(bg=hex_color)

    # ----------------------------------------------------------------
    # File operations
    # ----------------------------------------------------------------
    def upload_image(self):
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            img = Image.open(path).convert("RGB")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open image:\n{exc}")
            return

        self.image_path = path
        self.original_image = img.copy()
        self.image = img.copy()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.undo_btn.config(state="disabled")
        self.redo_btn.config(state="disabled")
        self.last_point = None

        if self.placeholder_id is not None:
            self.canvas.delete(self.placeholder_id)
            self.placeholder_id = None

        self._fit_zoom_to_window()
        self.redraw_canvas()

    def download_image(self):
        if self.image is None:
            messagebox.showinfo("No image", "Please upload an image first.")
            return
        default_name = "edited_image.png"
        if self.image_path:
            base = os.path.splitext(os.path.basename(self.image_path))[0]
            default_name = f"{base}_edited.png"
        path = filedialog.asksaveasfilename(
            title="Save image as",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            save_img = self.image
            if path.lower().endswith((".jpg", ".jpeg")):
                save_img = self.image.convert("RGB")
            save_img.save(path)
            messagebox.showinfo("Saved", f"Image saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not save image:\n{exc}")

    # ----------------------------------------------------------------
    # Canvas / zoom
    # ----------------------------------------------------------------
    def _fit_zoom_to_window(self):
        self.root.update_idletasks()
        cw = self.canvas.winfo_width() or 900
        ch = self.canvas.winfo_height() or 600
        iw, ih = self.original_image.size
        scale = min(cw / iw, ch / ih, 1.0)
        self.zoom = max(scale, 0.05)

    def redraw_canvas(self, fast=False):
        if self.image is None:
            return
        w, h = self.image.size
        disp_w = max(1, int(w * self.zoom))
        disp_h = max(1, int(h * self.zoom))
        if abs(self.zoom - 1.0) < 1e-6:
            resized = self.image
        else:
            resample = Image.NEAREST if fast else Image.LANCZOS
            resized = self.image.resize((disp_w, disp_h), resample)
        self.tk_image = ImageTk.PhotoImage(resized)

        # center the image in the canvas viewport when it's smaller than
        # the visible area, instead of always pinning it to the top-left
        canvas_w = self.canvas.winfo_width() or disp_w
        canvas_h = self.canvas.winfo_height() or disp_h
        x_off = max(0, (canvas_w - disp_w) // 2)
        y_off = max(0, (canvas_h - disp_h) // 2)
        self._img_offset = (x_off, y_off)

        self.canvas.delete("img")
        self.canvas.create_image(x_off, y_off, anchor="nw", image=self.tk_image, tags="img")
        scroll_w = max(canvas_w, disp_w)
        scroll_h = max(canvas_h, disp_h)
        self.canvas.config(scrollregion=(0, 0, scroll_w, scroll_h))

        self.zoom_label.config(text=f"{int(self.zoom * 100)}%")
        if hasattr(self, "zoom_slider"):
            self._zoom_sync_lock = True
            self.zoom_slider.set(int(round(self.zoom * 100)))
            self._zoom_sync_lock = False
        self._update_status()

    def zoom_in(self):
        if self.image is None:
            return
        self.zoom = min(self.zoom * 1.25, 8.0)
        self.redraw_canvas()

    def zoom_out(self):
        if self.image is None:
            return
        self.zoom = max(self.zoom / 1.25, 0.05)
        self.redraw_canvas()

    def _on_wheel_zoom(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _on_zoom_slider(self, value):
        if self._zoom_sync_lock or self.image is None:
            return
        self.zoom = max(0.05, float(value) / 100.0)
        self.redraw_canvas(fast=True)

    def _on_canvas_resize(self, _event=None):
        if self.image is not None:
            self.redraw_canvas(fast=True)
        elif self.placeholder_id is not None:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            self.canvas.coords(self.placeholder_id, w // 2, h // 2)

    def _canvas_to_image(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        x_off, y_off = self._img_offset
        return ((cx - x_off) / self.zoom, (cy - y_off) / self.zoom)

    # ----------------------------------------------------------------
    # Drawing (mouse events)
    # ----------------------------------------------------------------
    def on_press(self, event):
        if self.image is None:
            return
        if self.tool == "brush":
            # Crack tool: just remember where the drag started. The actual
            # crack is generated once, on release (see _apply_crack_stroke).
            self._crack_start_img = self._canvas_to_image(event)
            self._crack_start_canvas = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            self._clear_crack_preview()
            return
        self.push_undo()
        point = self._canvas_to_image(event)
        self.last_point = point
        self._erase_dab(point)
        self.redraw_canvas(fast=True)

    def on_drag(self, event):
        if self.image is None:
            return
        if self.tool == "brush":
            if self._crack_start_canvas is None:
                return
            # Live preview only (matches the original script's red dot +
            # green line) - the image itself isn't touched until release.
            self._clear_crack_preview()
            sx, sy = self._crack_start_canvas
            cx = self.canvas.canvasx(event.x)
            cy = self.canvas.canvasy(event.y)
            dot = self.canvas.create_oval(sx - 4, sy - 4, sx + 4, sy + 4,
                                           fill="#ff3b3b", outline="")
            line = self.canvas.create_line(sx, sy, cx, cy, fill="#34d058", width=2)
            self._crack_preview_ids = [dot, line]
            return
        if self.last_point is None:
            return
        point = self._canvas_to_image(event)
        self._erase_segment(self.last_point, point)
        self.last_point = point
        self.redraw_canvas(fast=True)

    def on_release(self, event):
        if self.tool == "brush":
            self._clear_crack_preview()
            start = self._crack_start_img
            self._crack_start_img = None
            self._crack_start_canvas = None
            if self.image is not None and start is not None:
                end = self._canvas_to_image(event)
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = float(np.hypot(dx, dy))
                if length >= 3:
                    angle = float(np.degrees(np.arctan2(dy, dx)))
                    self.push_undo()
                    self._apply_crack_stroke(start, angle, length)
            self.redraw_canvas(fast=False)
            return
        self.last_point = None
        self.redraw_canvas(fast=False)

    def _clear_crack_preview(self):
        for item_id in self._crack_preview_ids:
            self.canvas.delete(item_id)
        self._crack_preview_ids = []

    def _apply_crack_stroke(self, start_point, angle, length):
        """Runs the integrated crack_algorithm.py logic on the current
        image, starting at start_point and heading in the dragged
        direction/length. Brush Size sets the crack's max depth (thickness)."""
        depth = max(1, round(self.brush_size))
        arr = np.array(self.image)  # RGB uint8 HxWx3 - channel order doesn't
        draw_crack(arr, start_point[0], start_point[1], angle, length, depth=depth)
        self.image = Image.fromarray(arr)

    def _draw_dab(self, point):
        draw = ImageDraw.Draw(self.image)
        r = max(0.5, self.brush_size / 2)
        x, y = point
        draw.ellipse([x - r, y - r, x + r, y + r], fill=self.brush_color)

    def _draw_brush_segment(self, p0, p1):
        """Draws a plain straight stroke from p0 to p1 with rounded caps,
        so freehand drag motions look continuous instead of blocky."""
        draw = ImageDraw.Draw(self.image)
        w = max(1, round(self.brush_size))
        draw.line([p0, p1], fill=self.brush_color, width=w)
        r = w / 2
        for x, y in (p0, p1):
            draw.ellipse([x - r, y - r, x + r, y + r], fill=self.brush_color)

    def _erase_dab(self, point):
        if self.original_image is None:
            return
        x, y = point
        r = self.brush_size
        left, top = int(x - r), int(y - r)
        right, bottom = int(x + r), int(y + r)
        left, top = max(0, left), max(0, top)
        right = min(self.image.width, right)
        bottom = min(self.image.height, bottom)
        if right <= left or bottom <= top:
            return
        box = (left, top, right, bottom)
        mask = Image.new("L", (right - left, bottom - top), 0)
        ImageDraw.Draw(mask).ellipse(
            [x - left - r, y - top - r, x - left + r, y - top + r], fill=255
        )
        cur = self.image.crop(box)
        orig = self.original_image.crop(box)
        self.image.paste(Image.composite(orig, cur, mask), box)

    def _erase_segment(self, p0, p1):
        if self.original_image is None:
            return
        pad = self.brush_size + 4
        left = int(min(p0[0], p1[0]) - pad)
        top = int(min(p0[1], p1[1]) - pad)
        right = int(max(p0[0], p1[0]) + pad)
        bottom = int(max(p0[1], p1[1]) + pad)
        left, top = max(0, left), max(0, top)
        right = min(self.image.width, right)
        bottom = min(self.image.height, bottom)
        if right <= left or bottom <= top:
            return
        box = (left, top, right, bottom)
        mask = Image.new("L", (right - left, bottom - top), 0)
        rel_p0 = (p0[0] - left, p0[1] - top)
        rel_p1 = (p1[0] - left, p1[1] - top)
        ImageDraw.Draw(mask).line([rel_p0, rel_p1], fill=255, width=max(1, round(self.brush_size + 2)))
        cur = self.image.crop(box)
        orig = self.original_image.crop(box)
        self.image.paste(Image.composite(orig, cur, mask), box)

    # ----------------------------------------------------------------
    # History
    # ----------------------------------------------------------------
    def push_undo(self):
        if self.image is None:
            return
        self.undo_stack.append(self.image.copy())
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.undo_btn.config(state="normal")
        self.redo_btn.config(state="disabled")

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.image.copy())
        self.image = self.undo_stack.pop()
        self.redraw_canvas()
        self.redo_btn.config(state="normal")
        if not self.undo_stack:
            self.undo_btn.config(state="disabled")

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.image.copy())
        self.image = self.redo_stack.pop()
        self.redraw_canvas()
        self.undo_btn.config(state="normal")
        if not self.redo_stack:
            self.redo_btn.config(state="disabled")

    def reset_image(self):
        if self.original_image is None:
            messagebox.showinfo("No image", "Please upload an image first.")
            return
        if not messagebox.askyesno("Reset Image", "Discard all edits and reset to the original image?"):
            return
        self.push_undo()
        self.image = self.original_image.copy()
        self.redraw_canvas()

    def convert_to_bw(self):
        if self.image is None:
            messagebox.showinfo("No image", "Please upload an image first.")
            return
        self.push_undo()
        # convert to grayscale, then back to RGB so the rest of the app
        # (drawing, erasing, saving) keeps working exactly as before
        self.image = self.image.convert("L").convert("RGB")
        self.redraw_canvas()
        messagebox.showinfo("Success", "Image Converted Successfully")


def main():
    root = tk.Tk()
    ImagePainterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()