# Flower

A terminal animation inspired by a reference video: a growing, rotating bouquet made from colored ASCII characters. Also plays local video files as ASCII art or Unicode half-blocks.

The built-in bouquet is generated in Python; no video or image assets are required. It is an approximation of the reference animation, not a copy of its original 3D scene.

## Run

Install [uv](https://docs.astral.sh/uv/), then:

```sh
git clone https://github.com/Chychyndr/flower.git
cd flower
uv sync
uv run python ascii_player.py
```

Use Windows Terminal / PowerShell, macOS Terminal or a Linux terminal with ANSI truecolor support. A dark background and a small monospace font give the best result. Press Ctrl+C to exit.

## Options

```sh
uv run python ascii_player.py --width 120 --fps 30
uv run python ascii_player.py --mode blocks
uv run python ascii_player.py --no-color
uv run python ascii_player.py --once
uv run python ascii_player.py path/to/video.mp4 --once
```

Video playback is silent and loops by default. Terminal size is detected automatically. ASCII mode maps luminance to characters, applies optional Sobel edge detection, and emits RGB ANSI sequences. Block mode combines two vertical pixels per character. Only changed rows are redrawn.

## Tests

```sh
uv run pytest
```
