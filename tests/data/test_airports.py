from crewopt.data.airports import load_airports, tz_for


def test_known_airports_have_iana_time_zones():
    assert tz_for("DEN") == "America/Denver"
    assert tz_for("MCO") == "America/New_York"
    assert tz_for("HNL") == "Pacific/Honolulu"
    assert tz_for("SJU") == "America/Puerto_Rico"


def test_unknown_airport_returns_none():
    assert tz_for("ZZZ") is None


def test_reference_table_columns():
    df = load_airports()
    assert {"name", "lat", "lon", "tz"} <= set(df.columns)
    assert df.index.name == "code"
