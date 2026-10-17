"""Testes de schema e agregação."""

from __future__ import annotations

import pandas as pd
import pytest
from ingestion.aggregate import aggregate_cancer_deaths
from ingestion.cid import cancer_group, is_cancer
from ingestion.sample_data import build_synthetic_micro_mock, write_sample_bundle
from ingestion.schemas import validate_ibge_pop, validate_sim_agg


def test_aggregate_and_schema(tmp_path) -> None:
    micro = build_synthetic_micro_mock(seed=1, n_rows=800)
    micro["is_cancer"] = micro["causabas"].map(is_cancer)
    micro["cancer_group"] = micro["causabas"].map(cancer_group)
    cancer = micro.loc[micro["is_cancer"]]
    agg = aggregate_cancer_deaths(cancer, threshold=5)
    validate_sim_agg(agg)
    assert set(agg.columns) >= {
        "year",
        "uf",
        "sexo",
        "age_group",
        "cancer_group",
        "deaths",
        "suppressed",
    }
    # Células positivas < 5 devem estar NA
    small = agg.loc[agg["suppressed"]]
    if not small.empty:
        assert small["deaths"].isna().all()


def test_sample_bundle_schemas(tmp_path) -> None:
    paths = write_sample_bundle(tmp_path, seed=7)
    cancer = pd.read_parquet(paths["cancer_deaths_agg"])
    pop = pd.read_parquet(paths["ibge_population_sample"])
    validate_sim_agg(cancer)
    validate_ibge_pop(pop)
    assert len(cancer) > 0
    assert len(pop) > 0


def test_validate_sim_agg_rejects_bad_year() -> None:
    df = pd.DataFrame(
        {
            "year": [1800],
            "uf": ["SP"],
            "sexo": ["M"],
            "age_group": ["40-44"],
            "cancer_group": ["lung"],
            "deaths": [10],
            "suppressed": [False],
        }
    )
    with pytest.raises(ValueError):
        validate_sim_agg(df)
