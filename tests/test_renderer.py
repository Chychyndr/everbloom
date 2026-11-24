import re

import numpy as np
import pytest

from ascii_player import Renderer, bouquet

ANSI = re.compile(r"\x1b\[[0-9;]*m")


@pytest.mark.parametrize("mode", ["ascii", "blocks"])
@pytest.mark.parametrize("color", [True, False])
@pytest.mark.parametrize("shape", [(640, 640), (960, 320), (320, 960), (1, 1)])
def test_renderer_fits_terminal(mode, color, shape):
    frame = np.full((*shape, 3), 180, dtype=np.uint8)
    rows = Renderer(color, mode).convert(frame, 43, 17)
    assert len(rows) == 17
    assert all(len(ANSI.sub("", row)) <= 43 for row in rows)
    assert any(ANSI.sub("", row).strip() for row in rows)


def test_black_frame_is_blank():
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    assert not any(row.strip() for row in Renderer(False).convert(frame, 32, 16))


def test_bouquet_grows_and_moves():
    early = bouquet(1, 128)
    late = bouquet(12, 128)
    assert late.shape == (128, 128, 3)
    assert late.dtype == np.uint8
    assert np.count_nonzero(late) > np.count_nonzero(early)
    assert not np.array_equal(late, bouquet(13, 128))


def test_draw_skips_unchanged_rows(capsys):
    renderer = Renderer()
    renderer.draw(["hello"])
    assert "hello" in capsys.readouterr().out
    renderer.draw(["hello"])
    assert capsys.readouterr().out == ""
    renderer.draw(["world"])
    assert "world" in capsys.readouterr().out
