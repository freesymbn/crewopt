"""Scheduled local times ("hhmm" integers) → timestamps in UTC (research R2–R4).

BTS stores scheduled times as local "hhmm" integers (905 = 09:05, 2400 = midnight at the end of
the day). The arrival date is not given: we assume the flight date, and if that puts arrival at
or before departure in UTC, we move it to the next local day (midnight crossing).
"""

from __future__ import annotations

import pandas as pd


def parse_hhmm(value: int) -> tuple[int, int]:
    """Return (minutes since local midnight, day offset). 2400 → (0, 1)."""
    v = int(value)
    if v == 2400:
        return 0, 1
    hours, minutes = divmod(v, 100)
    if v < 0 or hours > 23 or minutes > 59:
        raise ValueError(f"invalid hhmm time: {value}")
    return hours * 60 + minutes, 0


def parse_hhmm_series(values: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Vectorised parse_hhmm; invalid values become <NA> in both outputs."""
    v = pd.to_numeric(values, errors="coerce").astype("Int64")
    hours, minutes = v // 100, v % 100
    valid = (v >= 0) & (((hours <= 23) & (minutes <= 59)) | (v == 2400))
    is_2400 = v == 2400
    mins = (hours * 60 + minutes).where(~is_2400, 0).where(valid)
    offset = is_2400.astype("Int64").where(valid)
    return mins.astype("Int64"), offset.astype("Int64")


def _localize_to_utc(local: pd.Series, tz: pd.Series) -> pd.Series:
    """Naive local timestamps + per-row IANA zone → UTC. Ambiguous/non-existent times → NaT."""
    out = pd.Series(pd.NaT, index=local.index, dtype="datetime64[ns, UTC]")
    for zone, idx in local.groupby(tz).groups.items():
        out.loc[idx] = (
            local.loc[idx]
            .dt.tz_localize(zone, ambiguous="NaT", nonexistent="NaT")
            .dt.tz_convert("UTC")
        )
    return out


def convert_schedule(df: pd.DataFrame) -> pd.DataFrame:
    """Add dep_local, arr_local (naive local wall time) and dep_utc, arr_utc.

    Input columns: flight_date (datetime64), crs_dep, crs_arr (hhmm), origin_tz, dest_tz.
    Rows with invalid times or non-existent/ambiguous local times get NaT.
    """
    out = df.copy()
    day = pd.to_datetime(out["flight_date"]).dt.normalize()

    dep_min, dep_off = parse_hhmm_series(out["crs_dep"])
    arr_min, arr_off = parse_hhmm_series(out["crs_arr"])

    def at(minutes: pd.Series, offset: pd.Series) -> pd.Series:
        return (
            day
            + pd.to_timedelta(minutes.astype("float"), unit="m")
            + pd.to_timedelta(offset.astype("float"), unit="D")
        )

    out["dep_local"] = at(dep_min, dep_off)
    out["dep_utc"] = _localize_to_utc(out["dep_local"], out["origin_tz"])

    arr_local = at(arr_min, arr_off)
    arr_utc = _localize_to_utc(arr_local, out["dest_tz"])

    # Midnight crossing: arrival not after departure → arrival is on the next local day.
    crossing = arr_utc.notna() & out["dep_utc"].notna() & (arr_utc <= out["dep_utc"])
    if crossing.any():
        arr_local = arr_local.where(~crossing, arr_local + pd.Timedelta(days=1))
        arr_utc.loc[crossing] = _localize_to_utc(arr_local[crossing], out.loc[crossing, "dest_tz"])

    out["arr_local"] = arr_local
    out["arr_utc"] = arr_utc
    return out
