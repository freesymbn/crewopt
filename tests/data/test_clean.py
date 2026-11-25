from datetime import date

import pandas as pd
import pytest

from crewopt.data.bts import read_raw
from crewopt.data.clean import clean


@pytest.fixture
def result(sample_csv):
    return clean(read_raw(sample_csv), carrier="F9", week_start=date(2026, 9, 14), buffer_days=3)


def test_exclusion_counts(result):
    assert result.counts == {
        "raw_rows": 20,
        "carrier_rows": 18,
        "in_window": 16,
        "excluded": {"cancelled": 1, "diverted": 1, "duplicate": 1, "bad_time": 1, "unknown_tz": 1},
        "final": 11,
        "buffer": 2,
    }


def test_flight_ids_are_stable_and_unique(result):
    f = result.flights
    assert f.flight_id.is_unique
    assert "F91003-20260914-DEN" in set(f.flight_id)


def test_buffer_flags(result):
    f = result.flights.set_index("flight_id")
    assert f.loc["F91011-20260921-DEN", "is_buffer"]
    assert f.loc["F91012-20260923-MCO", "is_buffer"]
    assert not f.loc["F91001-20260914-DEN", "is_buffer"]


def test_midnight_crossing_converted(result):
    row = result.flights.set_index("flight_id").loc["F91003-20260914-DEN"]
    assert row.dep_utc == pd.Timestamp("2026-09-15 04:30", tz="UTC")
    assert row.arr_utc == pd.Timestamp("2026-09-15 07:59", tz="UTC")
    assert row.block_minutes == 209


def test_missing_tail_is_kept(result):
    row = result.flights.set_index("flight_id").loc["F91010-20260917-DEN"]
    assert pd.isna(row.tail_number)


def test_sorted_by_departure_then_id(result):
    assert result.flights.dep_utc.is_monotonic_increasing


def test_schema(result):
    assert list(result.flights.columns) == [
        "flight_id",
        "carrier",
        "flight_number",
        "tail_number",
        "flight_date",
        "origin",
        "destination",
        "origin_tz",
        "dest_tz",
        "dep_local",
        "arr_local",
        "dep_utc",
        "arr_utc",
        "block_minutes",
        "crs_elapsed_minutes",
        "distance_miles",
        "is_buffer",
    ]


def test_empty_result_raises(sample_csv):
    with pytest.raises(ValueError, match="no flights"):
        clean(read_raw(sample_csv), carrier="XX", week_start=date(2026, 9, 14), buffer_days=3)
