import urllib.error

from crewopt.data import __main__ as cli
from crewopt.data import bts


def test_fetch_failure_prints_manual_instructions(monkeypatch, tmp_path, capsys):
    def boom(*args, **kwargs):
        raise urllib.error.URLError("blocked")

    monkeypatch.setattr(bts, "urlretrieve", boom)
    code = cli.main(["fetch", "--year", "2026", "--month", "8", "--dest", str(tmp_path)])
    err = capsys.readouterr().err
    assert code == 1
    assert "1987_present_2026_8.zip" in err
    assert str(tmp_path) in err


def test_compare_carriers_cli(sample_csv, config_file, capsys):
    code = cli.main(["compare-carriers", "--raw", str(sample_csv), "--config", str(config_file)])
    out = capsys.readouterr().out
    assert code == 0 and "F9" in out and "NK" in out
