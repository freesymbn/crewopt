"""Expected UTC values were computed independently with zoneinfo, not with crewopt code."""

from datetime import date

import pandas as pd
import pytest

from crewopt.data.timeconv import convert_schedule, parse_hhmm, parse_hhmm_series


# ---- hhmm parsing ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value, expected",
    [(905, (545, 0)), (0, (0, 0)), (1, (1, 0)), (2359, (1439, 0)), (2400, (0, 1))],
)
def test_parse_hhmm(value, expected):
    assert parse_hhmm(value) == expected  # (minutes since midnight, day offset)


@pytest.mark.parametrize("value", [1260, 2401, 2500, -5])
def test_parse_hhmm_rejects_invalid(value):
    with pytest.raises(ValueError):
        parse_hhmm(value)


def test_parse_hhmm_series_marks_invalid_as_na():
    minutes, offset = parse_hhmm_series(pd.Series([905, 2400, 1260]))
    assert minutes.tolist()[:2] == [545, 0]
    assert offset.tolist()[:2] == [0, 1]
    assert pd.isna(minutes.iloc[2])


# ---- local → UTC with arrival inference -------------------------------------------------------
def _frame(rows):
    return pd.DataFrame(
        rows, columns=["flight_date", "crs_dep", "crs_arr", "origin_tz", "dest_tz"]
    ).assign(flight_date=lambda d: pd.to_datetime(d.flight_date))


def _utc(s):
    return pd.Timestamp(s, tz="UTC")


def test_midnight_crossing_den_to_mco():
    out = convert_schedule(
        _frame([(date(2026, 9, 14), 2230, 359, "America/Denver", "America/New_York")])
    )
    assert out.dep_utc.iloc[0] == _utc("2026-09-15 04:30")
    assert out.arr_utc.iloc[0] == _utc("2026-09-15 07:59")  # next calendar day, local and UTC
    assert out.arr_local.iloc[0] == pd.Timestamp("2026-09-15 03:59")


def test_westbound_same_day_mco_to_den():
    out = convert_schedule(
        _frame([(date(2026, 9, 14), 800, 955, "America/New_York", "America/Denver")])
    )
    assert out.dep_utc.iloc[0] == _utc("2026-09-14 12:00")
    assert out.arr_utc.iloc[0] == _utc("2026-09-14 15:55")


def test_arrival_2400_means_midnight_next_day():
    out = convert_schedule(
        _frame([(date(2026, 9, 14), 2100, 2400, "America/Los_Angeles", "America/Los_Angeles")])
    )
    assert out.arr_utc.iloc[0] == _utc("2026-09-15 07:00")


def test_honolulu_no_dst():
    out = convert_schedule(
        _frame([(date(2026, 9, 15), 1300, 2130, "Pacific/Honolulu", "America/Los_Angeles")])
    )
    assert out.dep_utc.iloc[0] == _utc("2026-09-15 23:00")
    assert out.arr_utc.iloc[0] == _utc("2026-09-16 04:30")


def test_nonexistent_local_time_on_dst_start_is_nat():
    # 2026-03-08 02:30 does not exist in America/Denver (clocks jump 02:00 → 03:00)
    out = convert_schedule(
        _frame([(date(2026, 3, 8), 230, 500, "America/Denver", "America/Denver")])
    )
    assert pd.isna(out.dep_utc.iloc[0])


def test_ambiguous_local_time_on_dst_end_is_nat():
    # 2026-11-01 01:30 happens twice in America/Denver
    out = convert_schedule(
        _frame([(date(2026, 11, 1), 130, 500, "America/Denver", "America/Denver")])
    )
    assert pd.isna(out.dep_utc.iloc[0])
