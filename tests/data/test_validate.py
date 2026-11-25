from datetime import date

import pandas as pd
import pytest

from crewopt.data.bts import read_raw
from crewopt.data.clean import clean
from crewopt.data.validate import validate

PARAMS = dict(block_min=20, block_max=480, elapsed_tolerance=5, tail_continuity_min_share=0.95)


def _clean(path):
    return clean(read_raw(path), "F9", date(2026, 9, 14), 3).flights


@pytest.fixture
def good(sample_csv):
    return validate(_clean(sample_csv), **PARAMS)


@pytest.fixture
def bad(sample_csv):
    defects = sample_csv.parent / "bts_defects.csv"
    return validate(_clean(defects), **PARAMS)


def _check(report, check_id):
    return next(c for c in report.checks if c.id == check_id)


def test_clean_sample_is_valid(good):
    assert good.valid
    blocking = [c for c in good.checks if c.severity == "blocking"]
    assert len(blocking) == 4 and all(c.status == "pass" for c in blocking)


def test_report_has_all_checks(good):
    assert [c.id for c in good.checks] == [
        "arrival_after_departure",
        "block_time_range",
        "airports_known_and_distinct",
        "unique_ids",
        "tail_continuity",
        "tail_overlap",
        "elapsed_time_consistency",
        "missing_tail",
    ]


def test_defects_make_dataset_invalid(bad):
    assert not bad.valid


def test_origin_equals_destination_detected(bad):
    c = _check(bad, "airports_known_and_distinct")
    assert c.status == "fail" and "F92001-20260914-DEN" in c.examples


def test_block_time_out_of_range_detected(bad):
    c = _check(bad, "block_time_range")
    assert c.status == "fail" and "F92002-20260914-DEN" in c.examples


def test_duplicate_flight_id_detected(bad):
    c = _check(bad, "unique_ids")
    assert c.status == "fail" and c.count == 1 and "F92004-20260915-DEN" in c.examples


def test_wrong_time_zone_shows_as_elapsed_mismatch(bad):
    # LAS 06:00 → DEN 10:55 is 235 min, but schedule says 175: a 60-min (time-zone-sized) gap
    c = _check(bad, "elapsed_time_consistency")
    assert c.status == "warn" and "F92003-20260914-LAS" in c.examples


def test_tail_overlap_detected(bad):
    c = _check(bad, "tail_overlap")
    assert c.status == "warn" and c.count == 1


def test_tail_continuity_break_detected(bad):
    c = _check(bad, "tail_continuity")
    assert c.status == "warn" and any("F92008" in e for e in c.examples)


def test_missing_tail_reported(bad):
    c = _check(bad, "missing_tail")
    assert c.status == "warn" and c.count == 1


def test_arrival_before_departure_detected():
    f = pd.DataFrame(
        {
            "flight_id": ["X1"],
            "tail_number": ["N1"],
            "origin": ["DEN"],
            "destination": ["LAS"],
            "origin_tz": ["America/Denver"],
            "dest_tz": ["America/Los_Angeles"],
            "dep_utc": [pd.Timestamp("2026-09-14 15:00", tz="UTC")],
            "arr_utc": [pd.Timestamp("2026-09-14 14:00", tz="UTC")],
            "block_minutes": [-60],
            "crs_elapsed_minutes": [120],
        }
    )
    report = validate(f, **PARAMS)
    assert _check(report, "arrival_after_departure").status == "fail"
    assert not report.valid


def test_report_serializes(good):
    d = good.to_dict()
    assert d["valid"] is True and len(d["checks"]) == 8
