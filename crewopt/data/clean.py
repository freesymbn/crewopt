"""Select one carrier and week, drop unusable rows, convert to UTC (spec US1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from crewopt.data.airports import tz_for
from crewopt.data.timeconv import convert_schedule, parse_hhmm_series

COLUMNS = [
    "flight_id", "carrier", "flight_number", "tail_number", "flight_date",
    "origin", "destination", "origin_tz", "dest_tz",
    "dep_local", "arr_local", "dep_utc", "arr_utc",
    "block_minutes", "crs_elapsed_minutes", "distance_miles", "is_buffer",
]  # fmt: skip


@dataclass
class CleanResult:
    flights: pd.DataFrame
    counts: dict


def clean(raw: pd.DataFrame, carrier: str, week_start: date, buffer_days: int) -> CleanResult:
    counts: dict = {"raw_rows": len(raw)}
    excluded: dict[str, int] = {}

    df = raw[raw["carrier"] == carrier].copy()
    counts["carrier_rows"] = len(df)

    start = pd.Timestamp(week_start)
    buffer_start = start + pd.Timedelta(days=7)
    end = buffer_start + pd.Timedelta(days=buffer_days)  # exclusive
    df["flight_date"] = pd.to_datetime(df["flight_date"])
    df = df[(df["flight_date"] >= start) & (df["flight_date"] < end)]
    counts["in_window"] = len(df)
    if df.empty:
        raise ValueError(
            f"no flights for carrier {carrier} between {start:%Y-%m-%d} and {end:%Y-%m-%d}"
        )

    # Planning uses the published schedule: cancelled and diverted flights are not part of it.
    excluded["cancelled"] = int(df["cancelled"].sum())
    df = df[~df["cancelled"]]
    excluded["diverted"] = int(df["diverted"].sum())
    df = df[~df["diverted"]]

    before = len(df)
    df = df.drop_duplicates()
    excluded["duplicate"] = before - len(df)

    dep_min, _ = parse_hhmm_series(df["crs_dep"])
    arr_min, _ = parse_hhmm_series(df["crs_arr"])
    bad_time = (dep_min.isna() | arr_min.isna()).to_numpy()
    df = df[~bad_time]

    # Time zones are never guessed: unknown airport → flight excluded and reported.
    df = df.assign(origin_tz=df["origin"].map(tz_for), dest_tz=df["destination"].map(tz_for))
    unknown = (df["origin_tz"].isna() | df["dest_tz"].isna()).to_numpy()
    excluded["unknown_tz"] = int(unknown.sum())
    df = df[~unknown]

    df = convert_schedule(df)
    nat = (df["dep_utc"].isna() | df["arr_utc"].isna()).to_numpy()
    excluded["bad_time"] = int(bad_time.sum()) + int(nat.sum())
    df = df[~nat].copy()

    df["block_minutes"] = ((df["arr_utc"] - df["dep_utc"]).dt.total_seconds() // 60).astype(int)
    df["flight_id"] = (
        df["carrier"] + df["flight_number"].astype(str) + "-"
        + df["flight_date"].dt.strftime("%Y%m%d") + "-" + df["origin"]
    )  # fmt: skip
    df["is_buffer"] = df["flight_date"] >= buffer_start
    df["flight_date"] = df["flight_date"].dt.date
    df = df.rename(columns={"crs_elapsed": "crs_elapsed_minutes", "distance": "distance_miles"})

    df = df.sort_values(["dep_utc", "flight_id"], kind="mergesort")[COLUMNS].reset_index(drop=True)

    counts["excluded"] = {
        k: excluded[k] for k in ("cancelled", "diverted", "duplicate", "bad_time", "unknown_tz")
    }
    counts["final"] = len(df)
    counts["buffer"] = int(df["is_buffer"].sum())
    return CleanResult(flights=df, counts=counts)
