"""Data quality checks for the weekly flight table (spec US2, FR-013–FR-020).

Blocking checks decide whether the dataset may be used at all. Warning checks are reported with
counts and examples so a human can judge them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import pandas as pd

MAX_EXAMPLES = 10


@dataclass
class Check:
    id: str
    name: str
    severity: str  # "blocking" | "warning"
    status: str  # "pass" | "fail" | "warn"
    count: int = 0
    examples: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass
class ValidationReport:
    valid: bool
    checks: list[Check]

    def to_dict(self) -> dict:
        return {"valid": self.valid, "checks": [asdict(c) for c in self.checks]}


def _blocking(check_id: str, name: str, bad: pd.Series, ids: pd.Series, detail: str) -> Check:
    n = int(bad.sum())
    return Check(
        check_id, name, "blocking", "fail" if n else "pass", n,
        ids[bad].head(MAX_EXAMPLES).tolist(), detail,
    )  # fmt: skip


def _warning(check_id: str, name: str, n: int, examples: list[str], detail: str) -> Check:
    return Check(
        check_id, name, "warning", "warn" if n else "pass", n, examples[:MAX_EXAMPLES], detail
    )


def _tail_pairs(f: pd.DataFrame) -> pd.DataFrame:
    """Consecutive flights of the same aircraft: one row per (previous, next) pair."""
    t = f[f["tail_number"].notna()].sort_values(["tail_number", "dep_utc", "flight_id"])
    nxt = t.groupby("tail_number").shift(-1)
    pairs = pd.DataFrame({
        "prev_id": t["flight_id"], "next_id": nxt["flight_id"],
        "prev_dest": t["destination"], "next_origin": nxt["origin"],
        "prev_arr": t["arr_utc"], "next_dep": nxt["dep_utc"],
    })  # fmt: skip
    return pairs[pairs["next_id"].notna()]


def validate(
    flights: pd.DataFrame,
    *,
    block_min: int,
    block_max: int,
    elapsed_tolerance: int,
    tail_continuity_min_share: float,
) -> ValidationReport:
    f = flights
    ids = f["flight_id"]
    checks: list[Check] = []

    checks.append(_blocking(
        "arrival_after_departure", "Arrival after departure (UTC)",
        ~(f["arr_utc"] > f["dep_utc"]), ids, "FR-013",
    ))  # fmt: skip
    checks.append(_blocking(
        "block_time_range", f"Block time within {block_min}-{block_max} min",
        ~f["block_minutes"].between(block_min, block_max), ids, "FR-014",
    ))  # fmt: skip
    checks.append(_blocking(
        "airports_known_and_distinct", "Origin != destination, both with a time zone",
        (f["origin"] == f["destination"]) | f["origin_tz"].isna() | f["dest_tz"].isna(),
        ids, "FR-015",
    ))  # fmt: skip
    dup_ids = ids[ids.duplicated(keep=False)].drop_duplicates()
    checks.append(Check(
        "unique_ids", "Flight identifiers are unique", "blocking",
        "fail" if len(dup_ids) else "pass", len(dup_ids), dup_ids.head(MAX_EXAMPLES).tolist(),
        "FR-016",
    ))  # fmt: skip

    pairs = _tail_pairs(f)
    breaks = pairs[pairs["prev_dest"] != pairs["next_origin"]]
    share = 1.0 - len(breaks) / len(pairs) if len(pairs) else 1.0
    cont = _warning(
        "tail_continuity",
        "Aircraft continue from where they landed",
        len(breaks),
        (breaks["prev_id"] + " -> " + breaks["next_id"]).tolist(),
        f"FR-017; continuity share {share:.3f} over {len(pairs)} pairs "
        f"(target >= {tail_continuity_min_share})",
    )
    cont.status = "pass" if share >= tail_continuity_min_share else "warn"
    checks.append(cont)

    overlap = pairs[pairs["next_dep"] < pairs["prev_arr"]]
    checks.append(_warning(
        "tail_overlap", "Aircraft not scheduled on two flights at once",
        len(overlap), (overlap["prev_id"] + " x " + overlap["next_id"]).tolist(), "FR-018",
    ))  # fmt: skip

    diff = (f["block_minutes"] - f["crs_elapsed_minutes"]).abs()
    off = diff > elapsed_tolerance
    checks.append(_warning(
        "elapsed_time_consistency",
        f"Block time matches scheduled elapsed time (±{elapsed_tolerance} min)",
        int(off.sum()), ids[off].tolist(),
        "FR-019; a 60/120-minute gap usually means a time-zone error",
    ))  # fmt: skip

    missing = f["tail_number"].isna()
    checks.append(_warning(
        "missing_tail", "Tail number present", int(missing.sum()), ids[missing].tolist(), "FR-020",
    ))  # fmt: skip

    valid = all(c.status == "pass" for c in checks if c.severity == "blocking")
    return ValidationReport(valid, checks)
