"""Smoke test do baseline naive (requer dbt build prévio ou skip)."""

from __future__ import annotations

from pathlib import Path

import pytest
from forecasting.naive import run_naive_forecast

DUCKDB = Path("data/processed/cancer_mortality.duckdb")


@pytest.mark.skipif(not DUCKDB.exists(), reason="rode make dbt-build antes")
def test_naive_forecast_writes_parquet(tmp_path: Path) -> None:
    out = tmp_path / "forecast.parquet"
    summary = run_naive_forecast(duckdb_path=DUCKDB, output_path=out, horizon_year=2025)
    assert out.exists()
    assert summary["rows"] > 0
    assert summary["source_year"] >= 2020
