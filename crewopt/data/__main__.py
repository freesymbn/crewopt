"""Command-line interface for the data pipeline (contracts/cli.md).

uv run python -m crewopt.data build [--config config/data.yaml]
"""

from __future__ import annotations

import argparse
import sys

from crewopt.data.config import load_config
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
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m crewopt.data")
    sub = parser.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build", help="build the weekly flight dataset")
    p_build.add_argument("--config", default="config/data.yaml")
    p_build.set_defaults(func=_cmd_build)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
