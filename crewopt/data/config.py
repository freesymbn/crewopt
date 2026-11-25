"""Load and validate the Phase 1 data configuration (config/data.yaml)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import yaml

REQUIRED_SECTIONS = ("source", "selection", "validation", "exploration", "output")


@dataclass(frozen=True)
class DataConfig:
    raw_dir: Path
    raw_file: Path | None
    carrier: str
    carrier_selection_reason: str
    week_start: date
    buffer_days: int
    block_min: int
    block_max: int
    elapsed_tolerance: int
    tail_continuity_min_share: float
    base_max: int
    base_min_share: float
    candidate_carriers: tuple[str, ...]
    processed_dir: Path
    source_path: Path

    @property
    def week_end(self) -> date:
        """Last day (Sunday) of the selected week, inclusive."""
        return self.week_start + timedelta(days=6)

    @property
    def window_start(self) -> date:
        return self.week_start

    @property
    def window_end(self) -> date:
        """Last day of the selection window (week + buffer days), inclusive."""
        return self.week_end + timedelta(days=self.buffer_days)

    @property
    def dataset_id(self) -> str:
        return f"{self.carrier}_{self.week_start.isoformat()}"


def load_config(path: str | Path) -> DataConfig:
    path = Path(path)
    raw = yaml.safe_load(path.read_text()) or {}
    missing = [s for s in REQUIRED_SECTIONS if s not in raw]
    if missing:
        raise ValueError(f"config {path}: missing section(s): {', '.join(missing)}")

    sel, val, exp = raw["selection"], raw["validation"], raw["exploration"]
    week_start = sel["week_start"]
    if isinstance(week_start, str):
        week_start = date.fromisoformat(week_start)
    if week_start.weekday() != 0:
        raise ValueError(f"selection.week_start must be a Monday, got {week_start:%A} {week_start}")

    buffer_days = int(sel.get("buffer_days", 3))
    if buffer_days < 0:
        raise ValueError("selection.buffer_days must be >= 0")

    block = val["block_minutes"]
    if not 0 < int(block["min"]) < int(block["max"]):
        raise ValueError("validation.block_minutes must satisfy 0 < min < max")

    file = raw["source"].get("file")
    return DataConfig(
        raw_dir=Path(raw["source"]["raw_dir"]),
        raw_file=Path(file) if file else None,
        carrier=str(sel["carrier"]).strip().upper(),
        carrier_selection_reason=str(sel.get("carrier_selection_reason", "")),
        week_start=week_start,
        buffer_days=buffer_days,
        block_min=int(block["min"]),
        block_max=int(block["max"]),
        elapsed_tolerance=int(val["elapsed_tolerance_minutes"]),
        tail_continuity_min_share=float(val["tail_continuity_min_share"]),
        base_max=int(exp["base_max"]),
        base_min_share=float(exp["base_min_share"]),
        candidate_carriers=tuple(str(c).upper() for c in exp["candidate_carriers"]),
        processed_dir=Path(raw["output"]["processed_dir"]),
        source_path=path,
    )
