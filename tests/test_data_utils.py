import pandas as pd
import pytest
from src.utils.data_utils import load_dataset


def test_load_dataset_missing_file(monkeypatch, tmp_path):
    """If file is missing, ensure it retries and fails correctly."""

    fake_config = tmp_path / "fake_config.yaml"
    fake_data = tmp_path / "missing.csv"

    fake_config.write_text(f"data:\n  path: {fake_data}\nlogging:\n  log_dir: logs\nanalysis:\n  low_ctr_threshold: 0.01\n  min_impressions: 1000\n")

    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError):
        load_dataset(retries=2, delay=0.1)


def test_load_dataset_empty_file(monkeypatch, tmp_path):
    """Ensure empty CSV loads gracefully as an empty DataFrame."""

    f = tmp_path / "empty.csv"
    pd.DataFrame([]).to_csv(f, index=False)

    fake_config = tmp_path / "config.yaml"
    fake_config.write_text(f"data:\n  path: {f}\nlogging:\n  log_dir: logs\nanalysis:\n  low_ctr_threshold: 0.01\n  min_impressions: 1000\n")

    monkeypatch.chdir(tmp_path)

    df = load_dataset(retries=1)
    assert df.shape[0] == 0
