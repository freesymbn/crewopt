import json
import subprocess
import sys

import pandas as pd

from crewopt.data.config import load_config
from crewopt.data.pipeline import build


def test_build_writes_parquet_and_metadata(config_file):
    res = build(load_config(config_file))
    assert res.flights_path.exists() and res.meta_path.exists()
    assert res.flights_path.name == "flights_F9_2026-09-14.parquet"

    df = pd.read_parquet(res.flights_path)
    assert len(df) == 11
    assert str(df.dep_utc.dtype) == "datetime64[ns, UTC]"

    meta = json.loads(res.meta_path.read_text())
    assert meta["dataset_id"] == "F9_2026-09-14"
    assert meta["counts"]["final"] == 11
    assert meta["week_end"] == "2026-09-20" and meta["buffer_days"] == 3
    for key in ("source_sha256", "config_sha256", "data_sha256", "airportsdata_version"):
        assert len(str(meta[key])) > 0


def test_build_is_deterministic(config_file):
    a = build(load_config(config_file))
    sha_a = json.loads(a.meta_path.read_text())["data_sha256"]
    b = build(load_config(config_file))
    sha_b = json.loads(b.meta_path.read_text())["data_sha256"]
    assert sha_a == sha_b


def test_cli_build(config_file):
    proc = subprocess.run(
        [sys.executable, "-m", "crewopt.data", "build", "--config", str(config_file)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "final: 11" in proc.stdout


def test_build_writes_validation_report(config_file):
    res = build(load_config(config_file))
    report = json.loads(res.validation_path.read_text())
    assert report["valid"] is True
    assert json.loads(res.meta_path.read_text())["valid"] is True


def test_cli_exit_code_2_on_invalid_dataset(tmp_path, config_file):
    import yaml

    raw = yaml.safe_load(config_file.read_text())
    raw["source"]["file"] = raw["source"]["file"].replace("bts_sample.csv", "bts_defects.csv")
    bad_cfg = tmp_path / "bad.yaml"
    bad_cfg.write_text(yaml.safe_dump(raw))
    proc = subprocess.run(
        [sys.executable, "-m", "crewopt.data", "build", "--config", str(bad_cfg)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2, proc.stderr
    assert "valid: false" in proc.stdout


def test_build_writes_summary(config_file):
    res = build(load_config(config_file))
    assert "Crew-base proposal" in res.summary_path.read_text()
