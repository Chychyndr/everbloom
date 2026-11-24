"""Color ASCII video player and a procedural rotating flower bouquet."""
from __future__ import annotations

import argparse
import math
import os
import shutil
import sys
import time

import cv2
import numpy as np

RAMP = np.array(list(" .,:;irsXA253hMHGS#9B&@"))
TAU = math.tau


def bouquet(t: float, size: int = 640) -> np.ndarray:
    """Render a rotating bouquet in BGR without external assets."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    s = size / 640
    def pt(x, y):
        return round(x * s), round(y * s)
    def ellipse(x, y, rx, ry, angle, color):
        cv2.ellipse(img, pt(x, y), (max(1, round(rx*s)), max(1, round(ry*s))),
                    angle, 0, 360, color, -1, cv2.LINE_AA)
    def line(a, b, color, width):
        cv2.line(img, pt(*a), pt(*b), color, max(1, round(width*s)), cv2.LINE_AA)

    # Each new blossom grows into place over the first part of the cycle.
    phase = t % 22
    angle = t * 0.42
    flowers = []
    palette = [(123, 38, 220), (180, 60, 245), (218, 190, 245),
               (235, 150, 70), (70, 85, 245), (200, 100, 165)]
    for i in range(11):
        growth = min(1., max(0., (phase - i * 0.86) / 1.6))
        if growth <= 0:
            continue
        a = i * 2.39996 + angle
        radius = 0 if i == 0 else 80 + 8 * (i % 5)
        z = math.sin(a) * radius
        x = 320 + math.cos(a) * radius * growth
        y = 430 - (180 + 36 * math.sin(i * 1.75) + z * .38) * growth
        flowers.append((z, x, y, growth, i))

    # Stems and leaves, followed by blooms in depth order.
    for z, x, y, g, i in sorted(flowers):
        line((320 + (x-320)*.12, 487), (x, y), (40, 128, 42), 5)
        for side, offset in [(-1, .44), (1, .67)]:
            lx = 320 + (x-320)*offset
            ly = 487 + (y-487)*offset
            ellipse(lx+side*18*g, ly, 26*g, 9*g, side*35,
                    (37, 110 + i%3*21, 38))
    for z, x, y, g, i in sorted(flowers):
        base = palette[i % len(palette)]
        r = (39 + (i%3)*5) * g
        tilt = .65 + .3*math.sin(angle + i)
        for layer in range(2):
            count = 9 if layer == 0 else 6
            for j in range(count):
                a = TAU*j/count + i*.43 + layer*.6
                d = r * (.63 if layer == 0 else .31)
                shade = .69 + .29*(.5+.5*math.sin(a+1.3)) + .12*layer
                color = tuple(min(255, round(c*shade)) for c in base)
                ellipse(x+math.cos(a)*d, y+math.sin(a)*d*tilt,
                        r*(.57 if layer == 0 else .35),
                        r*(.27 if layer == 0 else .2),
                        math.degrees(a), color)
        ellipse(x, y, r*.23, r*.16, 0, (50, 170, 245))
        ellipse(x-2*g, y-2*g, r*.10, r*.08, 0, (90, 222, 255))

    # Vase with a curved silhouette and a moving highlight.
    vg = min(1., max(0., (phase-3)/2))
    if vg:
        for y in range(438, 575):
            u = (y-438)/137
            half = (29 + 30*math.sin(math.pi*u)**1.4)*vg
            for x in range(round(320-half), round(320+half)+1):
                nx = (x-320)/max(half, 1)
                light = .35 + .65*math.sqrt(max(0, 1-nx*nx))
                shine = .25*math.exp(-((nx+.35+.15*math.sin(angle))/.16)**2)
                color = tuple(min(255, int(c*(light+shine))) for c in (215, 105, 145))
                xx, yy = pt(x, y)
                if 0 <= xx < size and 0 <= yy < size:
                    img[yy, xx] = color
        ellipse(320, 438, 29*vg, 7, 0, (205, 150, 180))
        ellipse(320, 438, 22*vg, 3, 0, (32, 35, 49))
    # Sparse falling characters above the growing arrangement.
    for i in range(24):
        y = (t*90 + i*43) % 400
        x = 320 + 20*math.sin(i*1.8)
        if y < 130 + 40*math.sin(i):
            ellipse(x, y, 1, 2, 0, (75, 47, 32))
    return img


class Renderer:
    def __init__(self, color: bool = True, mode: str = "ascii", edges: float = .25):
        self.color = color
        self.mode = mode
        self.edges = edges
        self.previous: list[str] = []

    def convert(self, frame: np.ndarray, cols: int, rows: int) -> list[str]:
        """Fit an image inside a terminal grid, preserving visual aspect ratio."""
        h, w = frame.shape[:2]
        factor = min(cols/w, rows*(1 if self.mode == "blocks" else 2)/h)
        width = max(1, min(cols, round(w*factor)))
        height = max(1, min(rows*2, round(h*factor)))
        if self.mode == "ascii":
            height = max(1, min(rows, round(height/2)))
        else:
            height = max(2, min(rows*2, height + height%2))
        rgb = cv2.cvtColor(cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA),
                           cv2.COLOR_BGR2RGB)
        if self.mode == "blocks":
            lines = []
            for y in range(0, height, 2):
                parts = []
                for top, bottom in zip(rgb[y], rgb[y+1]):
                    if self.color:
                        a, b, c = map(int, top)
                        d, e, f = map(int, bottom)
                        parts.append(f"\x1b[38;2;{a};{b};{c};48;2;{d};{e};{f}m▀")
                    else:
                        k = int((top.mean()+bottom.mean())/2*(len(RAMP)-1)/255)
                        parts.append(str(RAMP[k]))
                lines.append("".join(parts)+"\x1b[0m" if self.color else "".join(parts))
        else:
            lum = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)/255
            indices = np.minimum(len(RAMP)-1, (np.sqrt(lum)*(len(RAMP)-1)).astype(int))
            glyphs = RAMP[indices].copy()
            if self.edges:
                gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
                gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
                magnitude = np.hypot(gx, gy)/4
                direction = ((np.degrees(np.arctan2(gy,gx))+90)%180/45).round().astype(int)%4
                mask = (magnitude > 1-self.edges*.8) & (lum > .07)
                glyphs[mask] = np.array(["-", "/", "|", "\\"])[direction[mask]]
            lines = []
            for y in range(height):
                parts = []
                last = None
                for x, glyph in enumerate(glyphs[y]):
                    if self.color and glyph != " ":
                        pixel = rgb[y,x].astype(float)
                        peak = max(1., pixel.max())
                        r,g,b = map(int, np.clip(pixel*(.65+.35*255/peak),0,255))
                        if (r,g,b) != last:
                            parts.append(f"\x1b[38;2;{r};{g};{b}m")
                            last = (r,g,b)
                    parts.append(str(glyph))
                lines.append("".join(parts)+("\x1b[0m" if self.color else ""))
        left = (cols-width)//2
        top = (rows-len(lines))//2
        return [""]*top + [" "*left + line for line in lines] + [""]*(rows-top-len(lines))

    def draw(self, lines: list[str]) -> None:
        """Update only changed rows, using ANSI cursor positioning."""
        output = []
        for i, row in enumerate(lines):
            if i >= len(self.previous) or self.previous[i] != row:
                output.append(f"\x1b[{i+1};1H\x1b[2K{row}")
        for i in range(len(lines), len(self.previous)):
            output.append(f"\x1b[{i+1};1H\x1b[2K")
        if output:
            sys.stdout.write("".join(output))
            sys.stdout.flush()
        self.previous = lines


def play(args: argparse.Namespace) -> None:
    cap = cv2.VideoCapture(args.video) if args.video else None
    if cap is not None and not cap.isOpened():
        cap.release()
        raise SystemExit(f"Cannot open video: {args.video}")
    if not sys.stdout.isatty():
        if cap is not None:
            cap.release()
        raise SystemExit("Run in an interactive terminal.")
    fps = args.fps or (cap.get(cv2.CAP_PROP_FPS) if cap is not None else 24)
    if not math.isfinite(fps) or fps <= 0:
        fps = 24
    if os.name == "nt":
        os.system("")  # Enable virtual terminal processing on modern Windows.
    renderer = Renderer(not args.no_color, args.mode, args.edges)
    start = time.monotonic()
    index = 0
    try:
        sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[2J\x1b[H")
        sys.stdout.flush()
        while True:
            if cap is None:
                t = index/fps
                if args.once and t >= 22:
                    break
                frame = bouquet(t)
            else:
                ok, frame = cap.read()
                if not ok:
                    if args.once:
                        break
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = cap.read()
                    if not ok:
                        break
            terminal = shutil.get_terminal_size((100, 40))
            cols = max(1, min(args.width, terminal.columns-1))
            rows = max(1, terminal.lines-1)
            renderer.draw(renderer.convert(frame, cols, rows))
            index += 1
            delay = start+index/fps-time.monotonic()
            if delay > 0:
                time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        if cap is not None:
            cap.release()
        sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", help="Optional input video")
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--mode", choices=["ascii", "blocks"], default="ascii")
    parser.add_argument("--edges", type=float, default=.25)
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--once", action="store_true", help="Play once, then exit")
    args = parser.parse_args()
    if args.width < 1 or (args.fps is not None and
                          (not math.isfinite(args.fps) or args.fps <= 0)):
        parser.error("width and fps must be positive")
    if not 0 <= args.edges <= 1:
        parser.error("edges must be between 0 and 1")
    play(args)


if __name__ == "__main__":
    main()
