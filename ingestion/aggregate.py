"""Agregação UF × sexo × faixa etária × grupo de câncer × ano (+ supressão)."""

from __future__ import annotations

import pandas as pd

from ingestion.schemas import SIM_AGG_COLUMNS, assert_columns, validate_sim_agg
from ingestion.suppression import suppress_small_counts


def aggregate_cancer_deaths(
    cancer_df: pd.DataFrame,
    *,
    threshold: int = 5,
    apply_suppression: bool = True,
) -> pd.DataFrame:
    """
    Agrega óbitos por câncer.

    Dimensões: year × uf × sexo × age_group × cancer_group
    """
    if cancer_df.empty:
        return pd.DataFrame(columns=list(SIM_AGG_COLUMNS))

    required = ["year", "uf", "sexo", "age_group", "cancer_group"]
    assert_columns(cancer_df, required, "cancer_df")

    work = cancer_df.dropna(subset=["cancer_group"]).copy()
    agg = work.groupby(required, as_index=False).size().rename(columns={"size": "deaths"})
    if apply_suppression:
        agg = suppress_small_counts(agg, count_col="deaths", threshold=threshold)
    else:
        agg["suppressed"] = False

    assert_columns(agg, SIM_AGG_COLUMNS, "sim_agg")
    return validate_sim_agg(agg)


def aggregate_ill_defined(ill_df: pd.DataFrame) -> pd.DataFrame:
    """Contagem de causas mal definidas por year × uf × sexo × age_group."""
    if ill_df.empty:
        return pd.DataFrame(columns=["year", "uf", "sexo", "age_group", "deaths_ill_defined"])
    return (
        ill_df.groupby(["year", "uf", "sexo", "age_group"], as_index=False)
        .size()
        .rename(columns={"size": "deaths_ill_defined"})
    )
