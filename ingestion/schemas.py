"""Schemas esperados dos artefatos Parquet (validação leve)."""

from __future__ import annotations

import pandas as pd

SIM_RAW_COLUMNS: tuple[str, ...] = (
    "year",
    "uf",
    "sexo",
    "idade_anos",
    "age_group",
    "causabas",
    "cancer_group",
    "is_cancer",
    "is_ill_defined",
    "codmunres",
)

SIM_AGG_COLUMNS: tuple[str, ...] = (
    "year",
    "uf",
    "sexo",
    "age_group",
    "cancer_group",
    "deaths",
    "suppressed",
)

ILL_DEFINED_AGG_COLUMNS: tuple[str, ...] = (
    "year",
    "uf",
    "sexo",
    "age_group",
    "deaths_ill_defined",
)

IBGE_POP_COLUMNS: tuple[str, ...] = (
    "year",
    "uf",
    "sexo",
    "age",
    "population",
)


def assert_columns(df: pd.DataFrame, required: tuple[str, ...] | list[str], name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{name}: colunas ausentes: {missing}")


def validate_sim_agg(df: pd.DataFrame) -> pd.DataFrame:
    assert_columns(df, SIM_AGG_COLUMNS, "sim_agg")
    if df.empty:
        return df
    if not df["year"].between(1996, 2100).all():
        raise ValueError("sim_agg: anos fora do intervalo esperado")
    return df


def validate_ibge_pop(df: pd.DataFrame) -> pd.DataFrame:
    assert_columns(df, IBGE_POP_COLUMNS, "ibge_pop")
    if df.empty:
        return df
    if (df["population"] < 0).any():
        raise ValueError("ibge_pop: população negativa")
    return df
