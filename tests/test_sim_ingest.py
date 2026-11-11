"""Testes de ingestão SIM com rede mockada."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from ingestion.sim import (
    SimDownloadError,
    download_sim_uf_year,
    filter_cancer_and_ill_defined,
    ingest_sim,
    transform_sim_microdata,
    write_sim_partitioned,
)


def _fake_sim_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CAUSABAS": ["C34", "C50", "R99", "I21", "C61"],
            "SEXO": [1, 2, 1, 1, 1],
            "IDADE": ["460", "455", "470", "440", "570"],
            "DTOBITO": ["15062020", "01012020", "31122020", "05052020", "09092020"],
            "CODMUNRES": ["355030", "355030", "355030", "355030", "355030"],
        }
    )


def test_transform_and_filter() -> None:
    raw = _fake_sim_df()
    transformed = transform_sim_microdata(raw, uf="SP", year=2020)
    assert set(["is_cancer", "is_ill_defined", "cancer_group", "age_group"]) <= set(
        transformed.columns
    )
    cancer, ill = filter_cancer_and_ill_defined(transformed)
    assert len(cancer) == 3  # C34, C50, C61
    assert len(ill) == 1  # R99
    assert set(cancer["cancer_group"]) == {"lung", "breast", "prostate"}


def test_write_partitioned(tmp_path: Path) -> None:
    raw = _fake_sim_df()
    transformed = transform_sim_microdata(raw, uf="SP", year=2020)
    cancer, _ = filter_cancer_and_ill_defined(transformed)
    paths = write_sim_partitioned(cancer, tmp_path / "sim_cancer")
    assert paths
    assert paths[0].exists()
    loaded = pd.read_parquet(paths[0])
    assert len(loaded) == 3


def test_download_retries_fallback() -> None:
    fake = _fake_sim_df()
    pysus = MagicMock()

    def _sim(**kwargs):
        if kwargs.get("source") == "catalog":
            raise RuntimeError("catalog timeout")
        return fake

    pysus.ftp.sim.side_effect = _sim

    with (
        patch("ingestion.sim._import_pysus", return_value=pysus),
        patch("ingestion.sim._download_sim_once") as once,
    ):

        def side_effect(pysus_mod, state, year, source):
            if source == "catalog":
                raise RuntimeError("catalog timeout")
            return fake

        once.side_effect = side_effect
        df = download_sim_uf_year("SP", 2020, sources=("catalog", "origin"))
    assert len(df) == 5


def test_download_all_sources_fail() -> None:
    with (
        patch("ingestion.sim._import_pysus", return_value=MagicMock()),
        patch("ingestion.sim._download_sim_once", side_effect=RuntimeError("boom")),
        pytest.raises(SimDownloadError),
    ):
        download_sim_uf_year("SP", 2020, sources=("catalog", "origin"))


def test_ingest_sim_with_mock(tmp_path: Path) -> None:
    fake = _fake_sim_df()
    with patch("ingestion.sim.download_sim_uf_year", return_value=fake):
        result = ingest_sim(years=[2020], ufs=["SP"], output_dir=tmp_path)
    assert result["cancer_rows"] == 3
    assert result["ill_defined_rows"] == 1
    assert Path(result["ill_defined_path"]).exists()
    assert result["partitions"]
