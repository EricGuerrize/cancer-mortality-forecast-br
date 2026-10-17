"""Demo offline: lê data/sample/ e valida schemas / agregações."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from ingestion.aggregate import aggregate_cancer_deaths
from ingestion.cid import cancer_group, is_cancer, is_ill_defined
from ingestion.config import get_settings
from ingestion.schemas import validate_ibge_pop, validate_sim_agg

logger = logging.getLogger(__name__)


def run_demo(sample_dir: Path | None = None) -> dict[str, Any]:
    """
    Executa o fluxo demonstrativo sem rede.

    Espera em `data/sample/`:
    - cancer_deaths_agg.parquet — agregados UF×sexo×idade×grupo×ano (já suprimidos)
    - ill_defined_counts.parquet — contagens R00–R99
    - ibge_population_sample.parquet — população IBGE (recorte)
    - (opcional) cancer_deaths_micro_mock.parquet — microdados sintéticos para re-agregar
    """
    settings = get_settings()
    root = sample_dir or settings.sample
    if not root.exists():
        raise FileNotFoundError(f"Diretório de amostra não encontrado: {root}")

    cancer_path = root / "cancer_deaths_agg.parquet"
    ill_path = root / "ill_defined_counts.parquet"
    pop_path = root / "ibge_population_sample.parquet"
    micro_path = root / "cancer_deaths_micro_mock.parquet"

    cancer = pd.read_parquet(cancer_path)
    validate_sim_agg(cancer)

    ill = pd.read_parquet(ill_path)
    pop = pd.read_parquet(pop_path)
    validate_ibge_pop(pop)

    # Reagrega a partir do mock (se presente) para exercitar a lógica localmente.
    reagg_rows = None
    if micro_path.exists():
        micro = pd.read_parquet(micro_path)
        micro = micro.copy()
        micro["is_cancer"] = micro["causabas"].map(is_cancer)
        micro["is_ill_defined"] = micro["causabas"].map(is_ill_defined)
        micro["cancer_group"] = micro["causabas"].map(cancer_group)
        reagg = aggregate_cancer_deaths(micro.loc[micro["is_cancer"]], threshold=5)
        reagg_rows = int(len(reagg))
        validate_sim_agg(reagg)

    summary = {
        "cancer_agg_rows": int(len(cancer)),
        "cancer_agg_years": sorted(cancer["year"].unique().tolist()),
        "cancer_agg_ufs": sorted(cancer["uf"].unique().tolist()),
        "ill_defined_rows": int(len(ill)),
        "population_rows": int(len(pop)),
        "suppressed_cells": int(cancer["suppressed"].fillna(False).sum()),
        "reaggregated_rows": reagg_rows,
        "sample_dir": str(root),
    }
    logger.info("Demo OK: %s", summary)
    return summary
