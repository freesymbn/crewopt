from datetime import date
from pathlib import Path

import pytest

from crewopt.data.config import DataConfig, load_config

ROOT = Path(__file__).resolve().parents[2]


def test_loads_project_config():
    cfg = load_config(ROOT / "config" / "data.yaml")
    assert isinstance(cfg, DataConfig)
    assert cfg.carrier == "F9"
    assert cfg.week_start == date(2026, 9, 14)
    assert cfg.buffer_days == 3
    assert cfg.block_min == 20 and cfg.block_max == 480


def test_window_covers_week_plus_buffer():
    cfg = load_config(ROOT / "config" / "data.yaml")
    assert cfg.window_start == date(2026, 9, 14)
    assert cfg.week_end == date(2026, 9, 20)
    assert cfg.window_end == date(2026, 9, 23)  # inclusive, 3 buffer days


def test_rejects_week_start_that_is_not_monday(tmp_path):
    text = (ROOT / "config" / "data.yaml").read_text().replace("2026-09-14", "2026-09-15")
    p = tmp_path / "data.yaml"
    p.write_text(text)
    with pytest.raises(ValueError, match="Monday"):
        load_config(p)


def test_rejects_missing_section(tmp_path):
    p = tmp_path / "data.yaml"
    p.write_text("selection:\n  carrier: F9\n")
    with pytest.raises(ValueError, match="missing"):
        load_config(p)
