"""Airport reference: IATA code → name, coordinates and IANA time zone (research R1)."""

from __future__ import annotations

from functools import cache

import airportsdata
import pandas as pd


@cache
def _iata() -> dict:
    return airportsdata.load("IATA")


@cache
def load_airports() -> pd.DataFrame:
    rows = [
        {"code": code, "name": a["name"], "lat": a["lat"], "lon": a["lon"], "tz": a["tz"]}
        for code, a in _iata().items()
    ]
    return pd.DataFrame(rows).set_index("code").sort_index()


def tz_for(code: str) -> str | None:
    """IANA time zone of an airport, or None if unknown. Never guesses (spec FR-015)."""
    entry = _iata().get(code)
    return entry["tz"] if entry and entry.get("tz") else None
