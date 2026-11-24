"""Baseline naive: carrega a última ASR observada para anos futuros (placeholder semana 3)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DUCKDB = Path("data/processed/cancer_mortality.duckdb")
DEFAULT_OUTPUT = Path("data/processed/naive_forecast.parquet")


def run_naive_forecast(
    *,
    duckdb_path: Path | str = DEFAULT_DUCKDB,
    output_path: Path | str = DEFAULT_OUTPUT,
    horizon_year: int = 2030,
) -> dict[str, Any]:
    """
    Lê `marts.fct_age_standardized_rates` e projeta a última ASR por série
    (uf × sexo × cancer_group) até `horizon_year` (hold-last-value).
    """
    db = Path(duckdb_path)
    out = Path(output_path)
    if not db.exists():
        raise FileNotFoundError(f"DuckDB não encontrado em {db}. Rode `make dbt-build` antes.")

    con = duckdb.connect(str(db), read_only=True)
    try:
        asr = con.execute(
            """
            select year, uf, sexo, cancer_group, cancer_group_label, asr_per_100k, deaths
            from marts.fct_age_standardized_rates
            """
        ).df()
    finally:
        con.close()

    if asr.empty:
        raise ValueError("fct_age_standardized_rates está vazio — nada a projetar.")

    last_year = int(asr["year"].max())
    latest = asr.loc[asr["year"] == last_year].copy()
    years = list(range(last_year + 1, horizon_year + 1))
    if not years:
        years = [last_year]

    frames: list[pd.DataFrame] = []
    for year in years:
        chunk = latest.copy()
        chunk["year"] = year
        chunk["method"] = "naive_last_value"
        chunk["source_year"] = last_year
        frames.append(chunk)

    forecast = pd.concat(frames, ignore_index=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    forecast.to_parquet(out, index=False)

    summary = {
        "rows": int(len(forecast)),
        "source_year": last_year,
        "years": years,
        "output": str(out),
    }
    logger.info("Naive forecast OK: %s", summary)
    return summary
