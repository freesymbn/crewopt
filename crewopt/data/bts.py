"""Read a raw BTS On-Time Performance month file (research R5)."""

from __future__ import annotations

import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

# BTS column name → our name. Only these columns are read.
COLUMN_MAP = {
    "FlightDate": "flight_date",
    "Reporting_Airline": "carrier",
    "Tail_Number": "tail_number",
    "Flight_Number_Reporting_Airline": "flight_number",
    "Origin": "origin",
    "Dest": "destination",
    "CRSDepTime": "crs_dep",
    "CRSArrTime": "crs_arr",
    "CRSElapsedTime": "crs_elapsed",
    "Cancelled": "cancelled",
    "Diverted": "diverted",
    "Distance": "distance",
}
REQUIRED_COLUMNS = tuple(COLUMN_MAP)

PREZIP_URL = (
    "https://transtats.bts.gov/PREZIP/"
    "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
)


def _read_csv(handle) -> pd.DataFrame:
    return pd.read_csv(
        handle,
        usecols=list(REQUIRED_COLUMNS),
        dtype={
            "Reporting_Airline": "string",
            "Tail_Number": "string",
            "Origin": "string",
            "Dest": "string",
            "CRSDepTime": "Int64",
            "CRSArrTime": "Int64",
            "Flight_Number_Reporting_Airline": "Int64",
        },
        low_memory=False,
    )


def read_raw(path: str | Path) -> pd.DataFrame:
    """Read a month file (.csv, or the BTS .zip that also contains a readme)."""
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            members = [m for m in zf.namelist() if m.lower().endswith(".csv")]
            if len(members) != 1:
                raise ValueError(f"{path}: expected exactly one .csv inside, found {members}")
            with zf.open(members[0]) as fh:
                df = _read_csv(fh)
    else:
        df = _read_csv(path)

    df = df.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())]
    df["cancelled"] = df["cancelled"].fillna(0).astype(float) > 0
    df["diverted"] = df["diverted"].fillna(0).astype(float) > 0
    df["crs_elapsed"] = df["crs_elapsed"].round().astype("Int64")
    df["distance"] = df["distance"].round().astype("Int64")
    df["tail_number"] = df["tail_number"].str.strip().replace("", pd.NA)
    return df


def fetch(year: int, month: int, dest: str | Path) -> Path:
    """Download a BTS month file. Raises OSError with manual-download instructions on failure."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    url = PREZIP_URL.format(year=year, month=month)
    target = dest / url.rsplit("/", 1)[-1]
    try:
        urlretrieve(url, target)
    except Exception as exc:  # network blocked, 404, timeout...
        raise OSError(
            f"download failed ({exc}).\n"
            f"Download it manually in a browser:\n  {url}\n"
            f"and save the zip into:\n  {dest}"
        ) from exc
    return target
