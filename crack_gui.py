"""
Image Painter
================
A small desktop GUI for freehand drawing/annotating on top of an
uploaded image. Useful for mocking up "damage" on photos (pavement,
walls, concrete, etc.), manual annotation, or quick image touch-ups.

Right-hand panel (top to bottom):
    Upload Image        - load a photo to draw on (top of panel)
    Brush / Erase        - stamp a procedural crack / restore original pixels
    Brush Size slider     - 0.25 to 20, sets the crack's max thickness (depth)
    Brush Color picker    - choose the brush's drawing color (see note below)
    Undo / Redo / Reset    - step back, step forward, or discard all edits
    Zoom  -  / +          - zoom the canvas out / in (also at the bottom-left
                            of the canvas, with a slider)
    Download Image       - save the result to disk (bottom of panel)

Brush tool: click, drag, and release to stamp a procedurally generated
crack (Perlin-noise jittered path, darkened into the image like a real
crack/shadow) along the direction and length you dragged. A live red-dot
+ green-line preview shows the direction while dragging; the crack itself
is only generated on release. The Brush Color picker does not affect this
crack effect (the algorithm darkens existing pixels rather than painting
a flat color) - it's left in the panel in case it's wanted for other uses.

Requirements:
    pip install pillow opencv-python numpy

Run:
    python image_painter.py
"""

import os
import io
import math
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

# Embedded toolbar icons (small PNGs, base64-encoded so the script stays a
# single portable file with no external image dependencies).
# Brush icon: an original flat-style icon (drawn here, inspired by the
# user's brush-pen photo rather than embedding the photo itself).
BRUSH_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAADeElEQVR4nMWWW2gcVRjH/2fO2e5MLk3c7G5xM+5OZ9bdJrF2JW5rIrhYsTR0W2lhvRShVaRIFRSLKCgsPogo+CCIbwapQpuKleJDHvpQxjyVVktJainEdqO5bIKXdbvZJDNn9viwYxKVFtdM6P9pYC6/c+b7nXM+4A6FAKBAjgKQ7sQA6Hp+nCQSiWA0anxqGMmvwmF1KwBkMhm2bsRYzPhA1xOiu/t+0dvb90ckEs2ughIvWX/Va4EQgkqlMruwUPV3dqrfxOPJV0zT5Pl8nsDDuhIAUjweb7FtHGeMPmFZ1rwsywgEgs3l8u+fXL069jIAgXpdHS+AxP0gNC3+oSTR1xzHrlLK7FAo3DY/Xx0eG/v+IIASkGGAydcClFwYASAVCuPHHMc5KklMcRxHLhZnfpNl/0AqlR5pbW1NAiZfq0zkH9cUANe0+C5CyEkAd3HOfwkEOoKM+X6dnp58Zmbm57OZTIaZpum4g11r6jOIxWJdmnbvmK4nhKpqpZ6ebSKd7ue6Hn8RAPL5vIT/YfCtXmAAuKqqAcbkLyilA3WZlA2BQIevVCq9f+3a6JvusxKA2lqBwIqVRNOMjyllR23brjDGSCgUbq5W578eHb10CMDNRmS63fpy3PukUPjxJc75MUqpXKvVaLE4XZZlZX8qlTb9/ja9EZn+Sw1WyWTsA6TjhKCNc14JBkMtkiQVp6YmnyoWJ791ZbrtTBsoev23aZq2jRA2RAhNWtbSzfb29iZFaa7Nzc0cmZi4/ln9xPmyhlsY3KhlDADftEkPK4p0klL6qGVZZVlWmkKhEKNUendk5NzbhBAIIZY3lNVpdI/kAOjs7PW5QmF8l+PwQZ/Pt9GylhZt217cvv2htwYHPz8hhGhxgZ5t/MtrMBrV3tix42Fx+PALzpkzw4v9fY+ISCR6GgAy8PaII7lcjgLAzp2P54aGTld2794r2gLhsmEkFz7qeuwBADhV7yI8DQOAbHZ/Wu2M/hDZbCy9urlP/NTz7NTEg8/pAHAq5z2UAkC2N9vUp265b/iegRMXjQPiStfT46L/+VYAEMh72yu5e+tyhrU9+84bB25c3vLkhYu9R3x1KIin7QPc8zUP4B2gdi52SO6Qq+/5Kd3Qomx8PfLd3Yse81ayWpYb3QdTl5O5rcLj/uhfEQARf7d0fYErYI+FaSR/AtCQL5EjxoEYAAAAAElFTkSuQmCC"

# Eraser icon: an original flat-style icon (drawn here, not the watermarked
# stock preview image), designed to visually pair with the brush icon above.
ERASER_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAEv0lEQVR4nM2WXWwUVRTH/+fe2Y/a7ZbPoqRCQTDIRxBKIipxUywtoZqoZKsJlgcejBBNSDACwWTSJ0p48ImHGo0aTAgdDOFFCA1uKhrahEYDTSVYLS3QbUvbaXe33Z2duff40FYLLS0gJP6TeTz3d87/nHvuAP8HsWkKNk1BADgalSZM8eRg9zm8LhqVjx9mjsIulrxV3FlRdbLrjaqmzoqq2rOR8iIA4EjE+K8Mmgij6mp94dWKtWtmz/s53+8PjSgPudIHO+vEb6UTu4ovnD7HpilQXc0E8CMDGSAw44sNW8IVC55uDPsDK1JuNgvAYEDnSMPQYO7LpA+uOH/yCDBqcaVlqYcFCgAE0yQi4tfnF3w1L5izIullPSLyE5EQREZaedrVGotD4ZqObTtO1BQX51daloo9gsXE0agky1KtZe8eWBoKHx7IZjwCTTqIRy1Uc/wBw846V68lh3aWNJz5jaN1kqxKjQe0WJBlqTMvbV4Q9vkPDXuuBjDlNBJABBj9TsbLNXxrVuXN+ulKWeUOsioVM8M0H+zqGABQkDO7KCBkKKMUCyKaLkAQGSnXVT4p8pbkhL5rLnl7HRHtB6CYWRLRtH0VANDlJNod5SWDUoIZMw4CEaQSxLe7e9SyD6v2DY0Mnvv++PFCIlLMPG1fBUejcvul+t5B1zkYEJJ8Qkg9A1T4DKT7bMKWV6Rve6kXDvpLy98s++Xqr40lROQxs2TmKZ0SZFmKTVOsrreOXR9ORBlsh30+qZm9KauTEm4ihVTRQhTu2wWMZIyUbaucYGDRsuXLz3e0te4lIkVEzMyT+ioAgKqrNUejcn29deqKbW9KednmuYGgwQzFE6ePCHA92JKw8NBuyGAA2vUgDEOOjIxoVp5c9NySz3vj7d+ae/aEiEjHYrG7LL6r7FgkYpQ0NHh7Vq4MfVq07lhBIGdnws2yYmZBJKSU6LvTj/BnuzG/fBNcOwEy/h1qZmYAOnfWHJm07ebWlpadG18rbZ04TJN8Hl9xANBaVrm3IPjUUUFkZAGV7O2T9N42PPtxFVx7CCSn3udaay8UDhvpdNq+1XHzg+dXrz81mjPpKRvLACEaFWRZ6vLmd0oW5+V/Y6TSi26/sNhbenS/wRln1N5ppLVWfr9f+oI56Gxv/6ho+epjzCynjeJIxKCGBu+HyNbCwoLCr9d8ebg04xPKS2eEkNPHAgAzq0AgINLpdOrS5cZl5eXbe2cOGlt9YJY93R1H5s+ds8/NZuFmXUWCZnwjtdbs9/up7dofG1dteLlpxnVElqVM0xRMpBc8U/RJ+5833leMZG5eSGqtp7w6E2GBYJAdx0m13W6/MRNrEpuZJQA0xWIvJuz4FWaHU3bcTdlxPTzYzfd+KTvuMjvccb3lAACMxz+Uxu9VbU1Nfl9PxwnmDA8PduvkQJeaCEsOdLnMDnd3tp0ag40+hY+iurq6fzK9+de1/elUv3bTNicHutyUHVfJgbij3SQP9t36vba2Np+Z6X6r7oE1dogAgJbmpq3DQz1dzC5rZ4iZszycuJO8eOHc2gnVPR6Nvw6xs6eL7sQ7aof6u5r6ejpPNjf+WPzYYeOaaPE9yTy5/1nTNMXYzgQziycKexj9Da9PoY8wpvZRAAAAAElFTkSuQmCC"


# Color-section icons (from user-provided brush-photo and color-picker
# artwork; backgrounds removed so they sit cleanly on the dark buttons).
COLOR_BRUSH_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAFFElEQVR42rWUf0zUZRjAn/f9vvc9uV9wHiBgQUje8Axdkau5EDATPMVUdkxQWyO7iaNTQ7CSdbFKjcQIHfPmFpJz1Z3gqo2kZHma8atWzWMRNnfHL/sOhBB2Hsf3vk9/6Dm2pqKe79/P+3z2PM/neQg8wmdNT2cVTqdYuHHt04nipR8Q0UsfFcxuMnEVTqe49ZWNCxNvdHxrjJ/QoejT0UcFy3M4AkVFWxbEjZ4/a9L75nb0+aGX078ecpjJZOIAALZv3/7kO2tiey+VRuA3hWrcljXvSyAc0FDDHA5HwGKxxId7vv4+T+97fGhcmvqxb9a1RSu2WAADNOSVlZZa4/YYH+v+bWcEthZrfNbscHz71cyCYKtDY6PVSgEArLW10btXJ7jad2iwc5fW9+GqMHxzffJXlMnAZIIQwz49odmRndD5c3E4/lGinTywapb0xvIYT11dXQQAUAQgoYKR5t9Racl+4vy5Ig12lWn9lavloiVDg/uLVq+Y3u6HeohAAIAgosySnXjmrDkcu/fMnvpknXKqOE2Ou9cv3AdAwZoObPo/8qCwPALUjojFxvmOVXFDG/RRnNjc4yc9//g5qo69WH3GvSyPEOIAkAAAg3/p/cOQZBDgHFQWKDYuOLY8ZnhD8hxOdF6Zot3CJCVyzTXD8y8XEEIkgxVwOuxBHwHCwGxMOXhyUzh69mr99flqybJUPrUrIxw/ML+UE7IVsKanM7sL+WLj/NLPNyrRvVc39cVmNe5Im+XfnanEdzc9+/7NuaWzO+Xg7sNIVlFfL6Yl63bGJy/6OIEMSJ7+q/RiLwR4DmX87IRT+xq7i5aliaze6QncKQ+dqf4VFRViZWVlEqXw1sLnso4JqeXX26cWSFT0MlRG//TCgT83S6KfnnNC4G5zozOR5FYcVSoV3xkMBiE5fq4tWhc9kfTiVk42d3F3Sva2dUY9mbRarUAeVhKz2SwDAKipqTnpcDjaBUHY0tnZiY2NDXj0aK3LdvzESgAAuz0Uklit7Cas6rW645/1DQ8Pr2xtbRUaG0/hkSM15w4f3qcLySUxmUxcEFZVVbW4tvaI5/Lly1ltbW1/nT7diIcOHay32+18qCq7fX2ampo0NputpaWlJa+jo+NCQ0MDfvTR/veCccHDfd/Jb4lBMjIyqNPpFAsKCgrCwsIKEXFeZGQkzclZMzAwMLi0t7fXXFZWdsxut/Mmkyl4sm5fE0LIPYUhiEimB+bk5Jj9fr+tsLAQ3G43NDc3Q2rqM9djYmKzSkpK2mZg9F3BJGiizWaLLC8vX97U1HR8yZIlRJIk9Pl8xO1209TU1CvV1dVOj8ejYoyNy2SyfwFAIIT0EUL+RsSBqKgogRAi3atCNjg4mBsVFZXtcrlSHQ7HIp1Ox3k8Hml0dJTjeR4GBwchPz8/qb+/P8nr9QLP8yCKInAcB4gIiOhljLkFQXCOjIycoZReiIiIGL0jUK1WZ7lcrrX5+fnRPT09oFAogBBClUolMMYwMzMT9Ho9dnV1BRhjRC6Xg0wmIzzPcwqFAlQqlUKj0RjGx8cjJUmiHMcJANB+q3v/ay1TqVQHbTbbAGPsqdzc3ES1Wh2n1WoVMTEx6pSUFGowGEAURYKIlJCbAkuShIwxL8dxIwBwdWJi4he5XO7kOO5XQRD6giO96wpoNBoYGxtTAcAcAJgNALEAoBIEQUEI4SmlgIiThJAbHMeNUUoFSZKGtFrtECHEO9O1+A8vUzXwQHjypgAAAABJRU5ErkJggg=="

COLOR_PICKER_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAGh0lEQVR42uVWa2wcVxX+7r0zs0+vvX7HcZPWinh4URIwj9JS2UaW6tKEpMAMCJKKNlIhoiGF0qpA7LsT21VC1FYhQKWQIpKUiu6qIrQJIq2QvaKRAIVWVbAVqaQNSZuHX8mu17uz87iHH7GBxElIf9A/nH93dO/5zuOb8x3gfTZ2oxcJYFnT5Gb7OAMAZuf8/0lEBLBh2am9LxlmTFNY2WwAADt7e0Nrloc6NMZWBIoSKlqz8xZ7r0MExhho3t+w7BQTY400/+6GASljCmZlg1ce6KlO1VZ9W+fsXsHZsuqQjvFZB1OVUt1Hnnp5+grAyyrDsPA7vx7Y6A/v7PloW+S1+ri+VedsmRsEwYVyxSXgnHL0fzkjKTkRMQA4PbR63VhfbycDiGhhQvxaYMf77/pyS03osKGztilV9h1P+QAQ0TUDhHruepfIw0DMthVjjM4MrXq2tdrY3xDTh4/39X6CMRBJeRmGdmXPmJUNjvfddXtTlf6rQBGreCpgOlg8zoVXYZhx/RMe4ZgXjygA7Ki8d0MyhLVCFcbr4+Jrk8WKEzW08PSsGwaAbGqMXTVDApjZnqUX5apoVZT/UgMTXqAUY0B1xBBF5r6aL3k9z79eTi390YF7VtasLACg6ZKXi0QSdycT9fedK1IlFjLC71wo931w4PAfSUpuWZeT598ZDncK1p3zT+5mG5pqIssm33V8uOCJsM6nZrx9rX0H7wOg5suO0UuE0MLNg6cK/hMxoVbckmzoOTlx/vH2gcODl1pjB9fuYVcuME1T6AIPVCggXs8p0Rpi04F/tLXv4NeJQMOyU5NS8mzWBLNt9VL/1gMuGZO3yl3fK/qxMzNeKO+hagVJyTHaTlcjJJ9nGWOg/ttmP6BrvL3kKCAAR5ixUo3qA0BId4pueyRIpVLMylrBr7fs3OOp0Ju9g9u/dbj/By+4MCb/9Pb5leVAfzoNIA1AXiIMW1DSEYxwACoR58uTMcELJdcL6VwvFJ2zr49N5whgSI8EEmlmWXbw8y379yjd/8qJs25bdsu2Zx2qTN+ZfvzhOZ8nrzdMNADomjt4AVU7QcSb9cPENIEyuW9ZTx0qk5QcaWBsLMV2PHbgZ+F4fIPrTrtLW43zTnnix+bgY5uHpdS6ALW+iHo/HtUqnkchXWdFlC4etO3SZSVlds6Xkvjps8V9O/+28chz735f333iEex7+yEAwO6W1YLZTH1oaXJtpHrJxulSUGZ6nXHBoSfXDz20WUqpjQCK2bbSWppeSDQ1/j3Z2DCWXNzyZl1VgwUAnVJqV/z4I7zbzjkFN3baRYIVXR2OirSZ38lEzpzpCEwzI8hIrgm0BvBwQ2SqWNnxjcF1D2cyGQFA2bZNpvxJnGtaOxciwoWo5kJEAXYRABpTKbrapGGcuUcFJ5CquLFwfFEbLf6sbTPV3Lwk5it8bLqQf2byYt787tDnHpVScsuyFNDFAZAmZnuMUKjWd10fYHBmS55Tnj0GAO2jo3TFpOlSAMj3i4fKpcgTHBr3dUWqOTpgmubvd+26tbBp0/7btu1aX8AcA207TXK4S9jd3X67aRptHZ0DsxfHKT/+DoUiMXiO88bzfY++RUSMMaYAQMzD5XI2mWZG7NmzeurTd9yfMhprl8/wvBeuqmmNNX5ymVFpfjGT2VwmItbSslqfmfkq5XKMcnv3KlNmjO4vms9VNy7q0sNx0sIxgJQoFfL9b7zyu9cAaLlcTi2QJymJp9Ogb24bWVoVrj0muB7zPdcPRxN6xcv/2YsX7fKpC7nd9udLALBux75Y7aK67trmJelYbV1HeSYfAIRoIikKE+dH//LSMx2fqq31bNsmzEnVAvkwzYzIZq3gwa1H1saT9b9RykfguhWtUQ+R4cMrlU8p8v4hog64Jm7Ww+Gb9HAUejjikVJcMwxBhIpzIX/7wKqOv0oibs+V85oCnMmQsCwWbBo68qVoLPkLLWFUlfhkAEIgNM0QugYRdRAELoLAdylQerLlJhaKxeE5jpufOGttX/OZ35qZjMhaVnBDim9mSGQtFmzc8vKHIzcnh1gIa0LhOFcqgFIeRNQB1zmE0FAq5APO+Uh10+JYYfzcI9u/cMer80G/p53mPyN88Ok/rND0yN3g7OOco1FEHYCpc0Q4Wi4WDv30/nuOXe3dezYpJZeS+H/d7uZWDEnXv8tuHJg4ukb42EQXtY+mCQBSqRQbbWhgGOlSts3UnD/C/7X9E+w3G0V/YvuZAAAAAElFTkSuQmCC"


# ==========================================================================
# Crack-generation algorithm now lives in crack_algorithm.py (same folder
# as this script) and is imported below instead of being inline here.
# ==========================================================================
from crack_algorithm import (
    CRACK_DEPTH,
    PERLIN_SCALE,
    PERLIN_STRENGTH,
    THRESHOLD_LOW,
    THRESHOLD_HIGH,
    BLUR_KERNEL,
    EDGE_BLUR_KERNEL,
    fade,
    lerp,
    grad,
    perlin,
    make_perm,
    perlin_patch,
    _build_stroke_mask_alpha,
    draw_crack,
    draw_edge_stroke,
)


class RoundedButton(tk.Canvas):
    """A button-like widget with gently rounded corners.

    Plain tk.Button has no border-radius option, so this draws a rounded
    rectangle on a Canvas and places an icon on top of it, while behaving
    like a normal button (hover highlight, active/selected state, click).
    """

    def __init__(self, parent, image, command, bg_parent, base_bg, hover_bg,
                 active_bg, width=104, height=44, radius=14, border_color="#5a5a5a",
                 text=None, text_angle=0, font=("Arial", 16, "normal"), fg=TEXT_LIGHT,
                 active_border_color=None, icon_kind=None):
        super().__init__(parent, width=width, height=height, bg=bg_parent,
                          highlightthickness=0, cursor="hand2")
        self.command = command
        self.image_ref = image
        self.text = text
        self.text_angle = text_angle
        self.font = font
        self.fg = fg
        self.icon_kind = icon_kind  # None, "undo", or "redo" -> drawn as a vector arrow
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

    def _draw_arrow_icon(self, cx, cy, r, color, clockwise, width=3):
        """Draw a circular undo/redo arrow (arc + arrowhead) as vector shapes,
        so the icon always renders correctly regardless of font/glyph support.

        clockwise=True  -> "redo" icon (arrow curls to the right)
        clockwise=False -> "undo" icon (arrow curls to the left, mirror image)
        """
        # theta=0 is 3 o'clock; increasing theta sweeps clockwise on screen.
        start_deg, end_deg = -200, 70
        steps = 32
        pts = []
        for i in range(steps + 1):
            t = start_deg + (end_deg - start_deg) * i / steps
            if not clockwise:
                t = 180 - t  # mirror horizontally for undo
            rad = math.radians(t)
            x = cx + r * math.cos(rad)
            y = cy + r * math.sin(rad)
            pts.extend([x, y])
        self.create_line(pts, fill=color, width=width, smooth=True,
                          capstyle=tk.ROUND, joinstyle=tk.ROUND)

        # Arrowhead at the end of the arc, tangent to direction of travel.
        end_t = end_deg if clockwise else 180 - end_deg
        rad_end = math.radians(end_t)
        tip_x, tip_y = pts[-2], pts[-1]
        dirx, diry = -math.sin(rad_end), math.cos(rad_end)
        if not clockwise:
            dirx = -dirx  # mirror direction of travel too
        norm = math.hypot(dirx, diry)
        dirx, diry = dirx / norm, diry / norm
        ah_len, ah_w = r * 0.6, r * 0.45
        bx, by = tip_x - dirx * ah_len, tip_y - diry * ah_len
        px, py = -diry, dirx
        left = (bx + px * ah_w, by + py * ah_w)
        right = (bx - px * ah_w, by - py * ah_w)
        self.create_polygon(tip_x, tip_y, *left, *right, fill=color, outline=color)

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
        elif self.icon_kind in ("undo", "redo"):
            icon_fg = "#5a5a5a" if self._disabled else self.fg
            r = min(self._btn_w, self._btn_h) * 0.28
            self._draw_arrow_icon(cx, cy, r, icon_fg, clockwise=(self.icon_kind == "redo"))
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
        self.tool = "crack"            # "brush" | "erase" | "crack" | "edge" | "fill"
        self.brush_size = 1.0          # fractional sizes supported (min 0.25, step 0.25)
        self.brush_color = (30, 28, 26)  # near-black by default
        self.fill_threshold = 30       # paint-bucket color-match tolerance

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

        # ---- batch "Upload Folder" state (added; does not affect the
        # single-image "Upload Image" flow above) ----
        self.folder_paths = None       # list[str], one per loaded image
        self.folder_originals = None   # list[PIL.Image], untouched per-file
        self.folder_images = None      # list[PIL.Image], current edited state per-file
        self.folder_index = -1         # index into the above lists, or -1 if none

        self._build_ui()

    # ----------------------------------------------------------------
    # UI construction
    # ----------------------------------------------------------------
    def _build_ui(self):
        self._build_title_bar(self.root)
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(fill="both", expand=True)
        self._build_toolbar(main)
        self._build_canvas(main)

    def _build_title_bar(self, parent):
        """Top title bar spanning the whole window: Prev / image-number /
        Next navigation centered in the middle, using arrow symbols only."""
        bar = tk.Frame(parent, bg=BG_PANEL, height=54)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)

        tk.Frame(bar, bg="#3a3a3a", height=1).pack(side="bottom", fill="x")

        nav = tk.Frame(bar, bg=BG_PANEL)
        nav.place(relx=0.5, rely=0.5, anchor="center")

        self.folder_prev_btn = self._make_button(nav, "\u2039", self.prev_folder_image, width=3)
        self.folder_prev_btn.pack(side="left", padx=4)
        self.folder_prev_btn.config(state="disabled")

        self.folder_nav_label = tk.Label(
            nav, text="No images", bg=BG_PANEL, fg=TEXT_LIGHT,
            font=("Arial", 10, "normal"), width=12, anchor="center",
        )
        self.folder_nav_label.pack(side="left", padx=10)

        self.folder_next_btn = self._make_button(nav, "\u203a", self.next_folder_image, width=3)
        self.folder_next_btn.pack(side="left", padx=4)
        self.folder_next_btn.config(state="disabled")

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
            fill=TEXT_DIM, font=("Arial", 14),
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
            bg=BG_DARK, fg=TEXT_DIM, font=("Arial", 9),
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
                                    font=("Arial", 9, "normal"), width=4)
        self.zoom_label.pack(side="left", padx=(0, 8), pady=6)

    def _build_toolbar(self, parent):
        panel = tk.Frame(parent, bg=BG_PANEL, width=240)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        # ---- Download Image: pinned to the very bottom of the panel ----
        bottom = tk.Frame(panel, bg=BG_PANEL)
        bottom.pack(side="bottom", fill="x", padx=16, pady=(16, 32))
        tk.Frame(bottom, bg="#3a3a3a", height=1).pack(fill="x", pady=(0, 12))
        self.download_btn = self._make_button(bottom, "Download Image", self.download_image)
        self.download_btn.pack(fill="x")

        # ---- everything else flows from the top, filling the rest ----
        top = tk.Frame(panel, bg=BG_PANEL)
        top.pack(side="top", fill="both", expand=True)

        def section_title(text):
            tk.Label(top, text=text, bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Arial", 9, "normal")).pack(anchor="w", padx=16, pady=(18, 4))

        def separator():
            tk.Frame(top, bg="#3a3a3a", height=1).pack(fill="x", padx=16, pady=10)

        # ---- File: choosing Image or Folder from the dropdown opens the
        # matching dialog immediately ----
        tk.Label(top, text="CrackGeneratorGUI", bg=BG_PANEL, fg=TEXT_LIGHT,
                 font=("Arial", 13, "normal")).pack(anchor="w", padx=16, pady=(18, 0))

        self.upload_mode = tk.StringVar(value="Select_One")
        self.upload_mode_menu = tk.OptionMenu(
            top, self.upload_mode, "Image", "Folder",
            command=self._on_upload_mode_selected,
        )
        self.upload_mode_menu.config(
            bg=BTN_BG, fg=TEXT_LIGHT, activebackground=BTN_BG_HOVER,
            activeforeground=TEXT_LIGHT, relief="flat", bd=0,
            font=("Arial", 10), highlightthickness=0, cursor="hand2",
            anchor="w", padx=8, pady=6,
        )
        self.upload_mode_menu["menu"].config(
            bg=BTN_BG, fg=TEXT_LIGHT, activebackground=ACCENT,
            activeforeground=TEXT_LIGHT,
        )
        self.upload_mode_menu.pack(fill="x", padx=16, pady=(14, 4))

        separator()

        # ---- Tools ----
        section_title("TOOLS")
        self.brush_icon_img = self._load_icon(BRUSH_ICON_B64)
        self.erase_icon_img = self._load_icon(ERASER_ICON_B64)
        self.color_brush_icon_img = self._load_icon(COLOR_BRUSH_ICON_B64)
        self.color_picker_icon_img = self._load_icon(COLOR_PICKER_ICON_B64)

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
                 font=("Arial", 9)).pack(side="left")
        self.size_value_label = tk.Label(
            size_row, text=f"{self.brush_size:.2f}", bg=BG_PANEL, fg=TEXT_DIM, font=("Arial", 9)
        )
        self.size_value_label.pack(side="right")

        self.size_scale = tk.Scale(
            top, from_=0.25, to=20, resolution=0.25, digits=4, orient="horizontal",
            bg=BG_PANEL, fg=TEXT_LIGHT, troughcolor=BTN_BG, highlightthickness=0,
            activebackground=ACCENT, showvalue=False, command=self._on_size_change,
        )
        self.size_scale.set(self.brush_size)
        self.size_scale.pack(fill="x", padx=16, pady=(0, 4))

        separator()

        # ---- Color: Fill Brush + Color Picker choose the color, Color
        # scale (0-255) sets the shade the Crack tool blends toward ----
        section_title("COLOR")

        color_btns_row = tk.Frame(top, bg=BG_PANEL)
        color_btns_row.pack(fill="x", padx=16, pady=(0, 8))

        # This is the "Fill Brush" tool: like the paint-bucket/fill tool in
        # Paint, clicking inside the image after this is selected floods the
        # contiguous region under the cursor with the current brush color.
        self.color_brush_btn = RoundedButton(
            color_btns_row, self.color_brush_icon_img, lambda: self.select_tool("fill"),
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=ACCENT,
        )
        self.color_brush_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.color_picker_btn = RoundedButton(
            color_btns_row, self.color_picker_icon_img, self.pick_color,
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=ACCENT,
        )
        self.color_picker_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

        self._caption_row(top, ["Fill Brush", "Color Picker"])

        # ---- Color scale (0-255): target shade the Crack tool blends
        # toward. 0 = black (classic dark crack), 255 = white. ----
        colorscale_row = tk.Frame(top, bg=BG_PANEL)
        colorscale_row.pack(fill="x", padx=16, pady=(4, 0))
        tk.Label(colorscale_row, text="Color", bg=BG_PANEL, fg=TEXT_LIGHT,
                 font=("Arial", 9)).pack(side="left")
        self.colorscale_value_label = tk.Label(
            colorscale_row, text="0", bg=BG_PANEL, fg=TEXT_DIM, font=("Arial", 9)
        )
        self.colorscale_value_label.pack(side="right")

        self.color_scale_var = tk.IntVar(value=0)
        self.color_scale_widget = tk.Scale(
            top, from_=0, to=255, resolution=1, orient="horizontal",
            bg=BG_PANEL, fg=TEXT_LIGHT, troughcolor=BTN_BG, highlightthickness=0,
            activebackground=ACCENT, showvalue=False, variable=self.color_scale_var,
            command=self._on_colorscale_change,
        )
        self.color_scale_widget.pack(fill="x", padx=16, pady=(0, 4))

        # ---- Edge scale (0-255): black-to-white shade the Edge tool
        # paints. 0 = solid black, 255 = solid white (default). Raising
        # this while drawing makes the stroke visibly lighter right away. ----
        edgescale_row = tk.Frame(top, bg=BG_PANEL)
        edgescale_row.pack(fill="x", padx=16, pady=(4, 0))
        tk.Label(edgescale_row, text="Edge", bg=BG_PANEL, fg=TEXT_LIGHT,
                 font=("Arial", 9)).pack(side="left")
        self.edgescale_value_label = tk.Label(
            edgescale_row, text="255", bg=BG_PANEL, fg=TEXT_DIM, font=("Arial", 9)
        )
        self.edgescale_value_label.pack(side="right")

        self.edge_scale_var = tk.IntVar(value=255)
        self.edge_scale_widget = tk.Scale(
            top, from_=0, to=255, resolution=1, orient="horizontal",
            bg=BG_PANEL, fg=TEXT_LIGHT, troughcolor=BTN_BG, highlightthickness=0,
            activebackground=ACCENT, showvalue=False, variable=self.edge_scale_var,
            command=self._on_edgescale_change,
        )
        self.edge_scale_widget.pack(fill="x", padx=16, pady=(0, 4))

        separator()

        # ---- Edge / Crack tools live up here, right above History ----
        edit_tools_row = tk.Frame(top, bg=BG_PANEL)
        edit_tools_row.pack(fill="x", padx=16, pady=(0, 4))

        self.edge_btn = RoundedButton(
            edit_tools_row, None, lambda: self.select_tool("edge"),
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=ACCENT,
            text="Edge", font=("Arial", 9, "normal"),
        )
        self.edge_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.crack_btn = RoundedButton(
            edit_tools_row, None, lambda: self.select_tool("crack"),
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=ACCENT,
            text="Crack", font=("Arial", 10, "normal"),
        )
        self.crack_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

        separator()

        # ---- History: Undo / Redo / Reset, as icon buttons ----
        section_title("HISTORY")
        history_row = tk.Frame(top, bg=BG_PANEL)
        history_row.pack(fill="x", padx=16, pady=4)

        self.undo_btn = RoundedButton(
            history_row, None, self.undo,
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=BTN_BG,
            width=60, height=44, radius=0, icon_kind="undo",
        )
        self.undo_btn.pack(side="left", expand=True, fill="x", padx=(0, 3))
        self.redo_btn = RoundedButton(
            history_row, None, self.redo,
            bg_parent=BG_PANEL, base_bg=BTN_BG, hover_bg=BTN_BG_HOVER, active_bg=BTN_BG,
            width=60, height=44, radius=0, icon_kind="redo",
        )
        self.redo_btn.pack(side="left", expand=True, fill="x", padx=3)
        self.reset_btn = self._make_button(history_row, "", self.reset_image, width=3,
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
            bg=BG_PANEL, fg=TEXT_DIM, font=("Arial", 8), justify="left",
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
            relief="flat", bd=0, font=("Arial", 10), cursor="hand2",
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
            lbl = tk.Label(row, text=label, bg=BG_PANEL, fg=TEXT_DIM, font=("Arial", 8))
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
        for btn, tool in (
            (self.brush_btn, "brush"), (self.erase_btn, "erase"),
            (self.edge_btn, "edge"), (self.crack_btn, "crack"),
            (self.color_brush_btn, "fill"),
        ):
            btn.set_active(self.tool == tool)

    def _update_status(self):
        if self.image is None:
            self.status_label.config(text="No image loaded")
            return
        w, h = self.image.size
        name = os.path.basename(self.image_path) if self.image_path else "untitled"
        tool_names = {"brush": "Brush", "erase": "Erase", "edge": "Edge", "crack": "Crack"}
        tool = tool_names.get(self.tool, self.tool)
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

    def _on_colorscale_change(self, value):
        if hasattr(self, "colorscale_value_label"):
            self.colorscale_value_label.config(text=str(int(float(value))))

    def _on_edgescale_change(self, value):
        if hasattr(self, "edgescale_value_label"):
            self.edgescale_value_label.config(text=str(int(float(value))))

    def pick_color(self):
        """Color Picker button. Like pickcoloronline.com, this first tries
        a screen eyedropper: click 'Pick color', then click ANYWHERE on
        your screen (even outside this app) to sample that exact pixel,
        with a live HEX/RGB readout following your cursor as you move.
        Press Escape to cancel. If a screen grab isn't available on this
        platform, it falls back to the normal color-chooser dialog."""
        try:
            self._start_eyedropper()
        except Exception:
            self._pick_color_dialog()

    def _pick_color_dialog(self):
        """Fallback: the standard OS color-chooser dialog."""
        rgb, hex_color = colorchooser.askcolor(
            color=self._rgb_to_hex(self.brush_color), title="Choose brush color"
        )
        if rgb:
            self._apply_picked_color(tuple(int(c) for c in rgb))

    def _apply_picked_color(self, rgb):
        """Shared by both the eyedropper and the dialog fallback: sets the
        brush color and keeps the Crack/Edge grayscale sliders roughly
        matched to the picked color's brightness (same behavior as before)."""
        self.brush_color = tuple(int(c) for c in rgb)
        gray = int(round(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]))
        gray = max(0, min(255, gray))
        self.color_scale_var.set(gray)
        self.edge_scale_var.set(gray)
        if hasattr(self, "colorscale_value_label"):
            self.colorscale_value_label.config(text=str(gray))
        if hasattr(self, "edgescale_value_label"):
            self.edgescale_value_label.config(text=str(gray))

    def _start_eyedropper(self):
        """Screen-wide eyedropper (pickcoloronline.com-style): grabs a
        screenshot of the whole screen, shows it full-screen under the
        cursor so the app itself is out of the way, and lets you hover to
        preview the HEX/RGB of whatever pixel is under the mouse before
        clicking to confirm. Works across monitors/other windows, not just
        this app's canvas."""
        from PIL import ImageGrab

        self.root.withdraw()
        self.root.update()

        try:
            screenshot = ImageGrab.grab(all_screens=True)
        except TypeError:
            screenshot = ImageGrab.grab()

        self._eyedropper_shot = screenshot
        self._eyedropper_photo = ImageTk.PhotoImage(screenshot)

        overlay = tk.Toplevel(self.root)
        self._eyedropper_win = overlay
        overlay.attributes("-fullscreen", True)
        try:
            overlay.attributes("-topmost", True)
        except tk.TclError:
            pass
        overlay.configure(bg="black", cursor="crosshair")

        canvas = tk.Canvas(overlay, highlightthickness=0, bd=0, bg="black")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=self._eyedropper_photo, anchor="nw")

        readout = tk.Label(
            overlay, text="", font=("Arial", 11, "normal"),
            bd=1, relief="solid", padx=8, pady=4,
        )

        hint = tk.Label(
            overlay, text="Click to pick a color  \u2022  Esc to cancel",
            bg="#000000", fg="#ffffff", font=("Arial", 10), padx=10, pady=6,
        )
        hint.place(relx=0.5, rely=0.02, anchor="n")

        def sample(x, y):
            try:
                w, h = screenshot.size
                x = max(0, min(w - 1, x))
                y = max(0, min(h - 1, y))
                pixel = screenshot.getpixel((x, y))
                return tuple(pixel[:3])
            except Exception:
                return None

        def on_motion(event):
            rgb = sample(event.x, event.y)
            if rgb is None:
                return
            hexcol = "#%02x%02x%02x" % rgb
            fg = "#ffffff" if sum(rgb) < 400 else "#000000"
            readout.config(
                text=f" {hexcol}   RGB({rgb[0]}, {rgb[1]}, {rgb[2]}) ",
                bg=hexcol, fg=fg,
            )
            readout.place(x=event.x + 20, y=event.y + 20)

        def close_eyedropper():
            overlay.destroy()
            self.root.deiconify()

        def on_click(event):
            rgb = sample(event.x, event.y)
            close_eyedropper()
            if rgb is not None:
                self._apply_picked_color(rgb)

        def on_escape(_event=None):
            close_eyedropper()

        canvas.bind("<Motion>", on_motion)
        canvas.bind("<Button-1>", on_click)
        overlay.bind("<Escape>", on_escape)
        overlay.focus_force()

    # ----------------------------------------------------------------
    # File operations
    # ----------------------------------------------------------------
    def _on_upload_mode_selected(self, value):
        """Called the instant the FILE dropdown selection changes - opens
        the matching dialog (image file picker or folder picker) right
        away, no separate Upload button needed."""
        if value == "Folder":
            self.upload_folder()
        else:
            self.upload_image()

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

    # ----------------------------------------------------------------
    # Batch folder upload (added; single-image upload_image() above is
    # unchanged and still works exactly as before)
    # ----------------------------------------------------------------
    def upload_folder(self):
        directory = filedialog.askdirectory(title="Choose a folder of images")
        if not directory:
            return

        exts = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp")
        try:
            filenames = sorted(
                f for f in os.listdir(directory) if f.lower().endswith(exts)
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Could not read folder:\n{exc}")
            return

        if not filenames:
            messagebox.showinfo("No images", "No supported image files were found in that folder.")
            return

        loaded_paths, originals = [], []
        for fname in filenames:
            fpath = os.path.join(directory, fname)
            try:
                img = Image.open(fpath).convert("RGB")
            except Exception:
                continue
            loaded_paths.append(fpath)
            originals.append(img)

        if not originals:
            messagebox.showerror("Error", "None of the files in that folder could be opened as images.")
            return

        self.folder_paths = loaded_paths
        self.folder_originals = originals
        self.folder_images = [img.copy() for img in originals]
        self._load_folder_image(0)

    def _load_folder_image(self, idx):
        """Loads folder_images[idx] into the main canvas/editing state,
        reusing the same load path as upload_image()."""
        self.folder_index = idx
        self.image_path = self.folder_paths[idx]
        self.original_image = self.folder_originals[idx].copy()
        self.image = self.folder_images[idx].copy()
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
        self._update_folder_nav()

    def _save_current_into_folder(self):
        """Keeps in-progress edits when navigating away from an image,
        so switching back and forth doesn't lose work."""
        if self.folder_images is not None and self.image is not None and 0 <= self.folder_index < len(self.folder_images):
            self.folder_images[self.folder_index] = self.image.copy()

    def next_folder_image(self):
        if not self.folder_images or self.folder_index >= len(self.folder_images) - 1:
            return
        self._save_current_into_folder()
        self._load_folder_image(self.folder_index + 1)

    def prev_folder_image(self):
        if not self.folder_images or self.folder_index <= 0:
            return
        self._save_current_into_folder()
        self._load_folder_image(self.folder_index - 1)

    def _update_folder_nav(self):
        if not self.folder_images:
            self.folder_nav_label.config(text="")
            self.folder_prev_btn.config(state="disabled")
            self.folder_next_btn.config(state="disabled")
            return
        total = len(self.folder_images)
        self.folder_nav_label.config(text=f"{self.folder_index + 1} / {total}")
        self.folder_prev_btn.config(state="normal" if self.folder_index > 0 else "disabled")
        self.folder_next_btn.config(state="normal" if self.folder_index < total - 1 else "disabled")

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
        if self.tool in ("crack", "edge"):
            # Drag-stroke tools: just remember where the drag started. The
            # actual effect is generated once, on release (see
            # _apply_crack_stroke / _apply_edge_stroke).
            self._crack_start_img = self._canvas_to_image(event)
            self._crack_start_canvas = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            self._clear_crack_preview()
            return
        if self.tool == "fill":
            # Paint-bucket fill: single click, no drag - fills the
            # contiguous region under the cursor with the brush color.
            self.push_undo()
            point = self._canvas_to_image(event)
            self._flood_fill(point)
            self.last_point = None
            self.redraw_canvas(fast=False)
            return
        self.push_undo()
        point = self._canvas_to_image(event)
        self.last_point = point
        if self.tool == "brush":
            self._draw_dab(point)
        else:  # erase
            self._erase_dab(point)
        self.redraw_canvas(fast=True)

    def on_drag(self, event):
        if self.image is None:
            return
        if self.tool in ("crack", "edge"):
            if self._crack_start_canvas is None:
                return
            # Live preview only (red dot + green line) - the image itself
            # isn't touched until release.
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
        if self.tool == "brush":
            self._draw_brush_segment(self.last_point, point)
        else:  # erase
            self._erase_segment(self.last_point, point)
        self.last_point = point
        self.redraw_canvas(fast=True)

    def on_release(self, event):
        if self.tool in ("crack", "edge"):
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
                    if self.tool == "crack":
                        self._apply_crack_stroke(start, angle, length)
                    else:
                        self._apply_edge_stroke(start, angle, length)
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
        direction/length. Brush Size sets the crack's max depth (thickness);
        the Color scale (0-255) sets the shade the crack blends toward."""
        depth = max(1, round(self.brush_size))
        color = self.color_scale_var.get()
        arr = np.array(self.image)  # RGB uint8 HxWx3 - channel order doesn't
        draw_crack(arr, start_point[0], start_point[1], angle, length, depth=depth, color=color)
        self.image = Image.fromarray(arr)

    def _apply_edge_stroke(self, start_point, angle, length):
        """Runs draw_edge_stroke on the current image, starting at
        start_point and heading in the dragged direction/length. Brush
        Size sets the stroke's max depth (thickness); the Edge scale
        (0-255) sets the shade the detected edges blend toward."""
        depth = max(1, round(self.brush_size))
        edge_color = self.edge_scale_var.get()
        arr = np.array(self.image)
        draw_edge_stroke(arr, start_point[0], start_point[1], angle, length, depth=depth, edge_color=edge_color)
        self.image = Image.fromarray(arr)

    def _blend_region(self, box, mask_uint8, color):
        """Alpha-blends `color` into self.image over `box`, using
        mask_uint8 (0-255, already feathered/blurred) as the per-pixel
        alpha. This is the same soft alpha-compositing approach the
        Crack/Edge tools use, so Brush strokes blend into the image
        instead of stamping a flat, hard-edged paint-app color."""
        left, top, right, bottom = box
        arr = np.array(self.image)
        region = arr[top:bottom, left:right].astype(np.float32)
        alpha = (mask_uint8.astype(np.float32) / 255.0)[:, :, None]
        color_arr = np.array(color, dtype=np.float32)
        blended = region * (1.0 - alpha) + color_arr * alpha
        arr[top:bottom, left:right] = np.clip(blended, 0, 255).astype(np.uint8)
        self.image = Image.fromarray(arr)

    def _feather_sigma(self):
        # Softer edge on bigger brushes, but never so soft it disappears
        # on tiny ones.
        return max(0.6, self.brush_size * 0.12)

    def _flood_fill(self, point):
        """Paint-bucket fill, the same idea as the Fill tool in Paint:
        starting at the clicked pixel, floods the connected region of
        similar color with the current brush color, stopping at edges/
        outlines (e.g. a crack you already drew) the way a paint app's
        bucket tool does. self.fill_threshold controls how close a
        neighboring pixel's color must be to count as "the same region"."""
        if self.image is None:
            return
        x, y = int(round(point[0])), int(round(point[1]))
        w, h = self.image.size
        if not (0 <= x < w and 0 <= y < h):
            return
        ImageDraw.floodfill(self.image, (x, y), self.brush_color, thresh=self.fill_threshold)

    def _draw_dab(self, point):
        r = max(0.5, self.brush_size / 2)
        x, y = point
        pad = int(r + self._feather_sigma() * 3) + 2
        left, top = int(x - r) - pad, int(y - r) - pad
        right, bottom = int(x + r) + pad, int(y + r) + pad
        left, top = max(0, left), max(0, top)
        right = min(self.image.width, right)
        bottom = min(self.image.height, bottom)
        if right <= left or bottom <= top:
            return
        mask = Image.new("L", (right - left, bottom - top), 0)
        ImageDraw.Draw(mask).ellipse(
            [x - left - r, y - top - r, x - left + r, y - top + r], fill=255
        )
        mask_np = cv2.GaussianBlur(np.array(mask), (0, 0), sigmaX=self._feather_sigma())
        self._blend_region((left, top, right, bottom), mask_np, self.brush_color)

    def _draw_brush_segment(self, p0, p1):
        """Draws a soft, blended stroke from p0 to p1 with rounded caps,
        so freehand drag motions look continuous and feathered rather
        than a flat, hard-edged paint-app line."""
        w = max(1, round(self.brush_size))
        r = w / 2
        pad = int(r + self._feather_sigma() * 3) + 2
        left = int(min(p0[0], p1[0]) - pad)
        top = int(min(p0[1], p1[1]) - pad)
        right = int(max(p0[0], p1[0]) + pad)
        bottom = int(max(p0[1], p1[1]) + pad)
        left, top = max(0, left), max(0, top)
        right = min(self.image.width, right)
        bottom = min(self.image.height, bottom)
        if right <= left or bottom <= top:
            return
        mask = Image.new("L", (right - left, bottom - top), 0)
        mdraw = ImageDraw.Draw(mask)
        rel_p0 = (p0[0] - left, p0[1] - top)
        rel_p1 = (p1[0] - left, p1[1] - top)
        mdraw.line([rel_p0, rel_p1], fill=255, width=w)
        for x, y in (rel_p0, rel_p1):
            mdraw.ellipse([x - r, y - r, x + r, y + r], fill=255)
        mask_np = cv2.GaussianBlur(np.array(mask), (0, 0), sigmaX=self._feather_sigma())
        self._blend_region((left, top, right, bottom), mask_np, self.brush_color)

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