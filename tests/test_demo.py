"""Teste da demo offline."""

from __future__ import annotations

from pathlib import Path

from ingestion.demo import run_demo
from ingestion.sample_data import write_sample_bundle


def test_run_demo(tmp_path: Path) -> None:
    write_sample_bundle(tmp_path, seed=99)
    summary = run_demo(sample_dir=tmp_path)
    assert summary["cancer_agg_rows"] > 0
    assert summary["population_rows"] > 0
    assert summary["reaggregated_rows"] is not None
    assert summary["reaggregated_rows"] > 0
