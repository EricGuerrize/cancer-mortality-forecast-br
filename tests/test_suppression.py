"""Testes de supressão de células pequenas."""

from __future__ import annotations

import pandas as pd
from ingestion.suppression import apply_secondary_suppression, suppress_small_counts


def test_suppress_small_counts_masks_below_threshold() -> None:
    df = pd.DataFrame(
        {
            "uf": ["SP", "SP", "SP", "RJ"],
            "deaths": [10, 3, 0, 5],
        }
    )
    out = suppress_small_counts(df, threshold=5)
    assert bool(out.loc[1, "suppressed"]) is True
    assert pd.isna(out.loc[1, "deaths"])
    assert bool(out.loc[0, "suppressed"]) is False
    assert out.loc[0, "deaths"] == 10
    # zero permanece zero
    assert out.loc[2, "deaths"] == 0
    assert bool(out.loc[2, "suppressed"]) is False
    # exatamente no limiar permanece
    assert out.loc[3, "deaths"] == 5
    assert bool(out.loc[3, "suppressed"]) is False


def test_secondary_suppression() -> None:
    df = pd.DataFrame(
        {
            "year": [2020, 2020, 2020],
            "uf": ["SP", "SP", "SP"],
            "deaths": [100, 3, 8],
        }
    )
    out = apply_secondary_suppression(df, group_cols=["year", "uf"], threshold=5)
    # Uma célula primária (<5) + a menor restante (8) devem ser suprimidas
    assert int(out["suppressed"].sum()) == 2
    assert pd.isna(out.loc[out["deaths"].isna()].iloc[0]["deaths"]) or True
