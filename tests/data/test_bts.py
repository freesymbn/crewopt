import zipfile

from crewopt.data.bts import REQUIRED_COLUMNS, read_raw

EXPECTED = {
    "flight_date",
    "carrier",
    "tail_number",
    "flight_number",
    "origin",
    "destination",
    "crs_dep",
    "crs_arr",
    "crs_elapsed",
    "cancelled",
    "diverted",
    "distance",
}


def test_reads_only_required_columns_from_csv(sample_csv):
    df = read_raw(sample_csv)
    assert set(df.columns) == EXPECTED
    assert len(df) == 20
    assert df.crs_dep.iloc[0] == 700  # "0700" read as integer hhmm
    assert df.cancelled.dtype == bool


def test_reads_zip_with_extra_members(sample_csv, tmp_path):
    z = tmp_path / "month.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.write(sample_csv, "On_Time_Reporting.csv")
        zf.writestr("readme.html", "<html></html>")
    df = read_raw(z)
    assert len(df) == 20 and set(df.columns) == EXPECTED


def test_required_columns_are_bts_names():
    assert "CRSDepTime" in REQUIRED_COLUMNS and "Tail_Number" in REQUIRED_COLUMNS
