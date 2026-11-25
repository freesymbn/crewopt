from datetime import date

import pytest

from crewopt.data.bts import read_raw
from crewopt.data.clean import clean
from crewopt.data.explore import (
    compare_carriers,
    daily_rotation,
    propose_bases,
    render_comparison_md,
    render_summary_md,
    summarize,
)


@pytest.fixture
def flights(sample_csv):
    return clean(read_raw(sample_csv), "F9", date(2026, 9, 14), 3).flights


def test_summary_totals_match_dataset(flights):
    s = summarize(flights, base_max=3, base_min_share=0.5)
    assert s["total_flights"] == len(flights) == 11
    assert s["week_flights"] == 9 and s["buffer_flights"] == 2
    assert sum(s["flights_per_day"].values()) == 11
    assert s["tails"] == 6
    assert s["airports"] == 7


def test_base_proposal_rule(flights):
    # week flights: DEN has 5 of 9 departures (56%) → one base is enough to cover >= 50%
    assert [code for code, _ in propose_bases(flights, base_max=3, min_share=0.5)] == ["DEN"]
    # asking for 70% needs more airports, capped at base_max
    assert len(propose_bases(flights, base_max=2, min_share=0.7)) == 2


def test_daily_rotation_is_connected(flights):
    rot = daily_rotation(flights, "N301FR", date(2026, 9, 14))
    assert rot["flight_id"].tolist() == ["F91001-20260914-DEN", "F91002-20260914-MCO"]
    assert (rot["destination"].iloc[0]) == rot["origin"].iloc[1]


def test_summary_example_rotation(flights):
    s = summarize(flights, base_max=3, base_min_share=0.5)
    ex = s["example_rotation"]
    assert ex["tail"] == "N301FR" and ex["date"] == "2026-09-14" and ex["connected"] is True


def test_summary_markdown(flights):
    md = render_summary_md(summarize(flights, base_max=3, base_min_share=0.5), "F9_2026-09-14")
    assert "Crew-base proposal" in md and "DEN" in md


def test_compare_carriers(sample_csv):
    table = compare_carriers(read_raw(sample_csv), ["F9", "NK"])
    row = table.set_index("carrier")
    assert row.loc["F9", "flights"] == 17  # 18 rows minus 1 cancelled
    assert row.loc["NK", "flights"] == 1
    assert row.loc["F9", "tails"] == 9
    assert "F9" in render_comparison_md(table)
