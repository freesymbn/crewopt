"""Command-line interface for the data pipeline (contracts/cli.md).

uv run python -m crewopt.data build [--config config/data.yaml]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from crewopt.data import bts
from crewopt.data.config import load_config
from crewopt.data.explore import compare_carriers, render_comparison_md
from crewopt.data.pipeline import build


def _cmd_build(args: argparse.Namespace) -> int:
    res = build(load_config(args.config))
    c = res.metadata["counts"]
    print(f"dataset: {res.metadata['dataset_id']}")
    print(
        f"raw_rows: {c['raw_rows']}  carrier_rows: {c['carrier_rows']}  in_window: {c['in_window']}"
    )
    print("excluded: " + ", ".join(f"{k}={v}" for k, v in c["excluded"].items()))
    print(f"final: {c['final']}  (buffer: {c['buffer']})")
    print(f"flights: {res.flights_path}")
    print(f"metadata: {res.meta_path}")
    print(f"validation: {res.validation_path}")
    for c in res.validation.checks:
        if c.status != "pass":
            print(
                f"  [{c.severity}] {c.id}: {c.status} ({c.count}) e.g. {', '.join(c.examples[:3])}"
            )
    print(f"valid: {str(res.validation.valid).lower()}")
    return 0 if res.validation.valid else 2


def _cmd_fetch(args: argparse.Namespace) -> int:
    path = bts.fetch(args.year, args.month, args.dest)
    print(f"downloaded: {path}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    carriers = args.carriers.split(",") if args.carriers else list(cfg.candidate_carriers)
    raw = bts.read_raw(args.raw)
    table = compare_carriers(raw, [c.strip().upper() for c in carriers])
    month = pd.to_datetime(raw["flight_date"]).max()
    out = cfg.processed_dir / f"carrier_comparison_{month:%Y_%m}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    md = render_comparison_md(table)
    out.write_text(md)
    print(md)
    print(f"written: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m crewopt.data")
    sub = parser.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build", help="build the weekly flight dataset")
    p_build.add_argument("--config", default="config/data.yaml")
    p_build.set_defaults(func=_cmd_build)

    p_fetch = sub.add_parser("fetch", help="download a BTS month file")
    p_fetch.add_argument("--year", type=int, required=True)
    p_fetch.add_argument("--month", type=int, required=True)
    p_fetch.add_argument("--dest", default="data/raw/bts")
    p_fetch.set_defaults(func=_cmd_fetch)

    p_cmp = sub.add_parser("compare-carriers", help="compare candidate carriers in a month file")
    p_cmp.add_argument("--raw", type=Path, required=True)
    p_cmp.add_argument("--carriers", help="comma-separated, default from config")
    p_cmp.add_argument("--config", default="config/data.yaml")
    p_cmp.set_defaults(func=_cmd_compare)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
