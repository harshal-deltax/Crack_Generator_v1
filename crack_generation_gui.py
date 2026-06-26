"""
Image Painter
================
A small desktop GUI for freehand drawing/annotating on top of an
uploaded image. Useful for mocking up "damage" on photos (pavement,
walls, concrete, etc.), manual annotation, or quick image touch-ups.

Right-hand panel (top to bottom):
    Upload Image        - load a photo to draw on (top of panel)
    Brush / Erase        - freehand draw / restore original pixels
    Brush Size slider     - 0.25 to 20, in steps of 0.25 (supports hairline strokes)
    Brush Color picker    - choose the brush's drawing color
    Undo / Redo / Reset    - step back, step forward, or discard all edits
    Zoom  -  / +          - zoom the canvas out / in (also at the bottom-left
                            of the canvas, with a slider)
    Download Image       - save the result to disk (bottom of panel)

Requirements:
    pip install pillow

Run:
    python image_painter.py
"""

import os
import io
import base64
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

# Embedded toolbar icons (small PNGs, base64-encoded so the script stays a
# single portable file with no external image dependencies).
# Brush icon: an original flat-style icon (drawn here, inspired by the
# user's brush-pen photo rather than embedding the photo itself).
BRUSH_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAADeElEQVR4nMWWW2gcVRjH/2fO2e5MLk3c7G5xM+5OZ9bdJrF2JW5rIrhYsTR0W2lhvRShVaRIFRSLKCgsPogo+CCIbwapQpuKleJDHvpQxjyVVktJainEdqO5bIKXdbvZJDNn9viwYxKVFtdM6P9pYC6/c+b7nXM+4A6FAKBAjgKQ7sQA6Hp+nCQSiWA0anxqGMmvwmF1KwBkMhm2bsRYzPhA1xOiu/t+0dvb90ckEs2ughIvWX/Va4EQgkqlMruwUPV3dqrfxOPJV0zT5Pl8nsDDuhIAUjweb7FtHGeMPmFZ1rwsywgEgs3l8u+fXL069jIAgXpdHS+AxP0gNC3+oSTR1xzHrlLK7FAo3DY/Xx0eG/v+IIASkGGAydcClFwYASAVCuPHHMc5KklMcRxHLhZnfpNl/0AqlR5pbW1NAiZfq0zkH9cUANe0+C5CyEkAd3HOfwkEOoKM+X6dnp58Zmbm57OZTIaZpum4g11r6jOIxWJdmnbvmK4nhKpqpZ6ebSKd7ue6Hn8RAPL5vIT/YfCtXmAAuKqqAcbkLyilA3WZlA2BQIevVCq9f+3a6JvusxKA2lqBwIqVRNOMjyllR23brjDGSCgUbq5W578eHb10CMDNRmS63fpy3PukUPjxJc75MUqpXKvVaLE4XZZlZX8qlTb9/ja9EZn+Sw1WyWTsA6TjhKCNc14JBkMtkiQVp6YmnyoWJ791ZbrtTBsoev23aZq2jRA2RAhNWtbSzfb29iZFaa7Nzc0cmZi4/ln9xPmyhlsY3KhlDADftEkPK4p0klL6qGVZZVlWmkKhEKNUendk5NzbhBAIIZY3lNVpdI/kAOjs7PW5QmF8l+PwQZ/Pt9GylhZt217cvv2htwYHPz8hhGhxgZ5t/MtrMBrV3tix42Fx+PALzpkzw4v9fY+ISCR6GgAy8PaII7lcjgLAzp2P54aGTld2794r2gLhsmEkFz7qeuwBADhV7yI8DQOAbHZ/Wu2M/hDZbCy9urlP/NTz7NTEg8/pAHAq5z2UAkC2N9vUp265b/iegRMXjQPiStfT46L/+VYAEMh72yu5e+tyhrU9+84bB25c3vLkhYu9R3x1KIin7QPc8zUP4B2gdi52SO6Qq+/5Kd3Qomx8PfLd3Yse81ayWpYb3QdTl5O5rcLj/uhfEQARf7d0fYErYI+FaSR/AtCQL5EjxoEYAAAAAElFTkSuQmCC"

# Eraser icon: an original flat-style icon (drawn here, not the watermarked
# stock preview image), designed to visually pair with the brush icon above.
ERASER_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAEv0lEQVR4nM2WXWwUVRTH/+fe2Y/a7ZbPoqRCQTDIRxBKIipxUywtoZqoZKsJlgcejBBNSDACwWTSJ0p48ImHGo0aTAgdDOFFCA1uKhrahEYDTSVYLS3QbUvbaXe33Z2duff40FYLLS0gJP6TeTz3d87/nHvuAP8HsWkKNk1BADgalSZM8eRg9zm8LhqVjx9mjsIulrxV3FlRdbLrjaqmzoqq2rOR8iIA4EjE+K8Mmgij6mp94dWKtWtmz/s53+8PjSgPudIHO+vEb6UTu4ovnD7HpilQXc0E8CMDGSAw44sNW8IVC55uDPsDK1JuNgvAYEDnSMPQYO7LpA+uOH/yCDBqcaVlqYcFCgAE0yQi4tfnF3w1L5izIullPSLyE5EQREZaedrVGotD4ZqObTtO1BQX51daloo9gsXE0agky1KtZe8eWBoKHx7IZjwCTTqIRy1Uc/wBw846V68lh3aWNJz5jaN1kqxKjQe0WJBlqTMvbV4Q9vkPDXuuBjDlNBJABBj9TsbLNXxrVuXN+ulKWeUOsioVM8M0H+zqGABQkDO7KCBkKKMUCyKaLkAQGSnXVT4p8pbkhL5rLnl7HRHtB6CYWRLRtH0VANDlJNod5SWDUoIZMw4CEaQSxLe7e9SyD6v2DY0Mnvv++PFCIlLMPG1fBUejcvul+t5B1zkYEJJ8Qkg9A1T4DKT7bMKWV6Rve6kXDvpLy98s++Xqr40lROQxs2TmKZ0SZFmKTVOsrreOXR9ORBlsh30+qZm9KauTEm4ihVTRQhTu2wWMZIyUbaucYGDRsuXLz3e0te4lIkVEzMyT+ioAgKqrNUejcn29deqKbW9KednmuYGgwQzFE6ePCHA92JKw8NBuyGAA2vUgDEOOjIxoVp5c9NySz3vj7d+ae/aEiEjHYrG7LL6r7FgkYpQ0NHh7Vq4MfVq07lhBIGdnws2yYmZBJKSU6LvTj/BnuzG/fBNcOwEy/h1qZmYAOnfWHJm07ebWlpadG18rbZ04TJN8Hl9xANBaVrm3IPjUUUFkZAGV7O2T9N42PPtxFVx7CCSn3udaay8UDhvpdNq+1XHzg+dXrz81mjPpKRvLACEaFWRZ6vLmd0oW5+V/Y6TSi26/sNhbenS/wRln1N5ppLVWfr9f+oI56Gxv/6ho+epjzCynjeJIxKCGBu+HyNbCwoLCr9d8ebg04xPKS2eEkNPHAgAzq0AgINLpdOrS5cZl5eXbe2cOGlt9YJY93R1H5s+ds8/NZuFmXUWCZnwjtdbs9/up7dofG1dteLlpxnVElqVM0xRMpBc8U/RJ+5833leMZG5eSGqtp7w6E2GBYJAdx0m13W6/MRNrEpuZJQA0xWIvJuz4FWaHU3bcTdlxPTzYzfd+KTvuMjvccb3lAACMxz+Uxu9VbU1Nfl9PxwnmDA8PduvkQJeaCEsOdLnMDnd3tp0ag40+hY+iurq6fzK9+de1/elUv3bTNicHutyUHVfJgbij3SQP9t36vba2Np+Z6X6r7oE1dogAgJbmpq3DQz1dzC5rZ4iZszycuJO8eOHc2gnVPR6Nvw6xs6eL7sQ7aof6u5r6ejpPNjf+WPzYYeOaaPE9yTy5/1nTNMXYzgQziycKexj9Da9PoY8wpvZRAAAAAElFTkSuQmCC"


class ToolTip:
    """Small hover tooltip for Tk widgets (Tkinter has no built-in one)."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _event=None):
        if self.tip is not None or not self.text:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        try:
            tw.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=self.text, bg="#111111", fg="#f0f0f0", font=("Segoe UI", 8),
            padx=6, pady=3, relief="solid", bd=1,
        ).pack()

    def _hide(self, _event=None):
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None


class RoundedButton(tk.Canvas):
    """A button-like widget with gently rounded corners.

    Plain tk.Button has no border-radius option, so this draws a rounded
    rectangle on a Canvas and places an icon on top of it, while behaving
    like a normal button (hover highlight, active/selected state, click).
    """

    def __init__(self, parent, image, command, bg_parent, base_bg, hover_bg,
                 active_bg, width=104, height=44, radius=14, border_color="#5a5a5a"):
        super().__init__(parent, width=width, height=height, bg=bg_parent,
                          highlightthickness=0, cursor="hand2")
        self.command = command
        self.image_ref = image
        self.base_bg = base_bg
        self.hover_bg = hover_bg
        self.active_bg = active_bg
        self.border_color = border_color
        self._active = False
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
        pts = self._rounded_points(pad, pad, self._btn_w - pad, self._btn_h - pad, self._radius)
        self.create_polygon(pts, smooth=True, fill=color, outline=self.border_color, width=1)
        if self.image_ref is not None:
            self.create_image(self._btn_w // 2, self._btn_h // 2, image=self.image_ref)

    def _on_enter(self, _event=None):
        self._draw(self.hover_bg)

    def _on_leave(self, _event=None):
        self._draw(self.active_bg if self._active else self.base_bg)

    def _on_click(self, _event=None):
        if self.command:
            self.command()

    def _on_resize(self, event):
        self._btn_w, self._btn_h = event.width, event.height
        self._draw(self.active_bg if self._active else self.base_bg)

    def set_active(self, active):
        self._active = active
        self._draw(self.active_bg if active else self.base_bg)


class ImagePainterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CrackGeneratorApp")
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
        self.brush_size = 4.0          # fractional sizes supported (min 0.25, step 0.25)
        self.brush_color = (30, 28, 26)  # near-black by default

        self.undo_stack = []
        self.redo_stack = []
        self.max_undo = 40
        self.last_point = None
        self.placeholder_id = None
        self._zoom_sync_lock = False
        self._img_offset = (0, 0)

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
        ToolTip(zo_out_btn, "Zoom out")

        self.zoom_slider = tk.Scale(
            self.zoom_overlay, from_=5, to=400, resolution=5, orient="horizontal", length=130,
            bg=BG_PANEL, fg=TEXT_LIGHT, troughcolor=BTN_BG, highlightthickness=0,
            activebackground=ACCENT, showvalue=False, command=self._on_zoom_slider,
        )
        self.zoom_slider.set(int(self.zoom * 100))
        self.zoom_slider.pack(side="left", padx=4, pady=6)
        self.zoom_slider.bind("<ButtonRelease-1>", lambda e: self.redraw_canvas(fast=False))
        ToolTip(self.zoom_slider, "Drag to zoom")

        zo_in_btn = self._make_button(self.zoom_overlay, "+", self.zoom_in, width=3)
        zo_in_btn.pack(side="left", padx=(4, 6), pady=6)
        ToolTip(zo_in_btn, "Zoom in")

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
        ToolTip(self.download_btn, "Save the edited image to your computer")

        # ---- everything else flows from the top, filling the rest ----
        top = tk.Frame(panel, bg=BG_PANEL)
        top.pack(side="top", fill="both", expand=True)

        def section_title(text):
            tk.Label(top, text=text, bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(18, 4))

        def separator():
            tk.Frame(top, bg="#3a3a3a", height=1).pack(fill="x", padx=16, pady=10)

        tk.Label(top, text="CrackGeneratorApp", bg=BG_PANEL, fg=TEXT_LIGHT,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=16, pady=(18, 0))

        # ---- File: top only has Upload ----
        section_title("FILE")
        self.upload_btn = self._make_button(top, "\u2b06  Upload Image", self.upload_image)
        self.upload_btn.pack(fill="x", padx=16, pady=4)
        ToolTip(self.upload_btn, "Choose a photo to draw on")

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
        ToolTip(self.brush_btn, "Brush: draw freehand on the image")
        self.erase_btn = RoundedButton(
            tools_row, self.erase_icon_img, lambda: self.select_tool("erase"),
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=ACCENT,
        )
        self.erase_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))
        ToolTip(self.erase_btn, "Erase: restore the original pixels")

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
        ToolTip(self.size_scale, "Adjust brush thickness (0.25 - 20px)")

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
        ToolTip(self.color_swatch, "Click to pick a brush color")

        self._update_tool_buttons()

        separator()

        # ---- History: Undo / Redo / Reset, as icon buttons ----
        section_title("HISTORY")
        history_row = tk.Frame(top, bg=BG_PANEL)
        history_row.pack(fill="x", padx=16, pady=4)

        self.undo_btn = self._make_button(history_row, "\u21BA", self.undo, width=3)
        self.undo_btn.pack(side="left", expand=True, fill="x", padx=(0, 3))
        ToolTip(self.undo_btn, "Undo the last action")
        self.redo_btn = self._make_button(history_row, "\u21BB", self.redo, width=3)
        self.redo_btn.pack(side="left", expand=True, fill="x", padx=3)
        ToolTip(self.redo_btn, "Redo the last undone action")
        self.reset_btn = self._make_button(history_row, "\U0001F5D1", self.reset_image, width=3, danger=True)
        self.reset_btn.pack(side="left", expand=True, fill="x", padx=(3, 0))
        ToolTip(self.reset_btn, "Discard all edits, back to original")

        self.undo_btn.config(state="disabled")
        self.redo_btn.config(state="disabled")

        self._caption_row(top, ["Undo", "Redo", "Reset"])

        separator()

        # ---- Effects: convert the image to black & white ----
        section_title("EFFECTS")
        self.bw_btn = self._make_button(top, "\u25D1  Convert to B&W", self.convert_to_bw)
        self.bw_btn.pack(fill="x", padx=16, pady=4)
        ToolTip(self.bw_btn, "Convert the image to black & white")

        separator()

        tk.Label(
            top, text="Tip: click & drag on the image\nto draw or erase. Ctrl + scroll,\nor the slider below, also zooms.",
            bg=BG_PANEL, fg=TEXT_DIM, font=("Segoe UI", 8), justify="left",
        ).pack(anchor="w", padx=16, pady=(22, 10))

    def _make_button(self, parent, text, command, width=None, image=None, danger=False):
        base_bg = "#7a2020" if danger else BTN_BG
        hover_bg = "#9c2b2b" if danger else BTN_BG_HOVER
        kwargs = dict(
            command=command, bg=base_bg, fg=TEXT_LIGHT,
            activebackground=hover_bg, activeforeground=TEXT_LIGHT,
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
        Undo/Redo/Reset)."""
        row = tk.Frame(parent, bg=BG_PANEL)
        row.pack(fill="x", padx=16, pady=(0, 4))
        for label in labels:
            tk.Label(row, text=label, bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Segoe UI", 8)).pack(side="left", expand=True)

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
        self.push_undo()
        point = self._canvas_to_image(event)
        self.last_point = point
        if self.tool == "brush":
            self._draw_dab(point)
        else:
            self._erase_dab(point)
        self.redraw_canvas(fast=True)

    def on_drag(self, event):
        if self.image is None or self.last_point is None:
            return
        point = self._canvas_to_image(event)
        if self.tool == "brush":
            self._draw_brush_segment(self.last_point, point)
        else:
            self._erase_segment(self.last_point, point)
        self.last_point = point
        self.redraw_canvas(fast=True)

    def on_release(self, event):
        self.last_point = None
        self.redraw_canvas(fast=False)

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
        messagebox.showinfo(
            "Conversion Successful",
            "The image was converted to black & white.\nYou can now download it.",
        )


def main():
    root = tk.Tk()
    ImagePainterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()