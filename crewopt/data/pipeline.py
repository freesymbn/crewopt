"""Run the Phase 1 pipeline and write outputs with metadata (spec FR-010–FR-012)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import pandas as pd

import crewopt
from crewopt.data.bts import read_raw
from crewopt.data.clean import clean
from crewopt.data.config import DataConfig
from crewopt.data.explore import render_summary_md, summarize
from crewopt.data.validate import ValidationReport, validate


@dataclass
class BuildResult:
    flights: pd.DataFrame
    metadata: dict
    flights_path: Path
    meta_path: Path
    validation: ValidationReport
    validation_path: Path
    summary_path: Path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def data_checksum(flights: pd.DataFrame) -> str:
    """Canonical checksum of the flight table (research R6): independent of Parquet bytes."""
    return hashlib.sha256(flights.to_csv(index=False).encode()).hexdigest()


def resolve_raw_file(cfg: DataConfig) -> Path:
    if cfg.raw_file:
        return cfg.raw_file
    files = sorted(p for p in cfg.raw_dir.glob("*") if p.suffix.lower() in {".zip", ".csv"})
    if len(files) != 1:
        raise FileNotFoundError(
            f"expected exactly one .zip/.csv in {cfg.raw_dir}, found {len(files)}; "
            "set source.file in config/data.yaml or see data/README.md"
        )
    return files[0]


def build(cfg: DataConfig) -> BuildResult:
    raw_path = resolve_raw_file(cfg)
    result = clean(read_raw(raw_path), cfg.carrier, cfg.week_start, cfg.buffer_days)

    out_dir = cfg.processed_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    flights_path = out_dir / f"flights_{cfg.dataset_id}.parquet"
    meta_path = out_dir / f"flights_{cfg.dataset_id}.meta.json"

    validation_path = out_dir / f"flights_{cfg.dataset_id}.validation.json"

    result.flights.to_parquet(flights_path, index=False)
    report = validate(
        result.flights,
        block_min=cfg.block_min,
        block_max=cfg.block_max,
        elapsed_tolerance=cfg.elapsed_tolerance,
        tail_continuity_min_share=cfg.tail_continuity_min_share,
    )
    validation_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n")
    summary_path = out_dir / f"flights_{cfg.dataset_id}.summary.md"
    summary = summarize(result.flights, cfg.base_max, cfg.base_min_share)
    summary_path.write_text(render_summary_md(summary, cfg.dataset_id))

    metadata = {
        "dataset_id": cfg.dataset_id,
        "source_file": raw_path.name,
        "source_sha256": _sha256_file(raw_path),
        "carrier": cfg.carrier,
        "carrier_selection_reason": cfg.carrier_selection_reason,
        "week_start": cfg.week_start.isoformat(),
        "week_end": cfg.week_end.isoformat(),
        "buffer_days": cfg.buffer_days,
        "config_sha256": _sha256_file(cfg.source_path),
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "package_version": crewopt.__version__,
        "airportsdata_version": version("airportsdata"),
        "counts": result.counts,
        "data_sha256": data_checksum(result.flights),
        "valid": report.valid,
    }
    meta_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return BuildResult(
        result.flights, metadata, flights_path, meta_path, report, validation_path, summary_path
    )
