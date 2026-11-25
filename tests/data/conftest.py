from pathlib import Path

import pytest
import yaml

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sample_csv() -> Path:
    return FIXTURES / "bts_sample.csv"


@pytest.fixture
def config_file(tmp_path, sample_csv) -> Path:
    """Project config pointed at the sample fixture and a temporary output folder."""
    raw = yaml.safe_load((ROOT / "config" / "data.yaml").read_text())
    raw["source"]["file"] = str(sample_csv)
    raw["output"]["processed_dir"] = str(tmp_path / "processed")
    p = tmp_path / "data.yaml"
    p.write_text(yaml.safe_dump(raw))
    return p
