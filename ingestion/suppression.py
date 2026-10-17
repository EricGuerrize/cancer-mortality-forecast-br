"""Supressão de células pequenas (privacidade / ética estatística)."""

from __future__ import annotations

import pandas as pd

DEFAULT_THRESHOLD = 5


def suppress_small_counts(
    df: pd.DataFrame,
    *,
    count_col: str = "deaths",
    threshold: int = DEFAULT_THRESHOLD,
    flag_col: str = "suppressed",
) -> pd.DataFrame:
    """
    Suprime células com contagem < threshold.

    - Coluna de contagem vira NA (pandas NA / None) nas células pequenas
    - Coluna booleana `suppressed` indica se a célula foi ocultada
    - Células com 0 permanecem 0 (não há risco de identificação por rareza positiva)
    """
    if count_col not in df.columns:
        raise KeyError(f"Coluna de contagem ausente: {count_col}")

    out = df.copy()
    counts = pd.to_numeric(out[count_col], errors="coerce")
    mask = counts.gt(0) & counts.lt(threshold)
    out[flag_col] = mask.fillna(False)
    out.loc[mask, count_col] = pd.NA
    return out


def apply_secondary_suppression(
    df: pd.DataFrame,
    *,
    group_cols: list[str],
    count_col: str = "deaths",
    threshold: int = DEFAULT_THRESHOLD,
) -> pd.DataFrame:
    """
    Supressão secundária simples: se exatamente uma célula de um grupo está
    suprimida, suprime também a menor célula restante do mesmo grupo (evita
    reconstituição por diferença).
    """
    out = suppress_small_counts(df, count_col=count_col, threshold=threshold)
    if not group_cols:
        return out

    def _secondary(group: pd.DataFrame) -> pd.DataFrame:
        g = group.copy()
        suppressed = g["suppressed"].fillna(False)
        if int(suppressed.sum()) != 1:
            return g
        visible = g.loc[~suppressed, count_col]
        visible_num = pd.to_numeric(visible, errors="coerce")
        if visible_num.notna().sum() == 0:
            return g
        idx = visible_num.idxmin()
        g.loc[idx, count_col] = pd.NA
        g.loc[idx, "suppressed"] = True
        return g

    parts = [_secondary(g) for _, g in out.groupby(group_cols, dropna=False)]
    return pd.concat(parts, ignore_index=True) if parts else out
