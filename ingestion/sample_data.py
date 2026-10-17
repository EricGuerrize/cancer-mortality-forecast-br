"""Gera amostra agregada sintética (sem microdados reais / sem PII) para demo e CI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ingestion.age import AGE_GROUPS, age_to_group
from ingestion.aggregate import aggregate_cancer_deaths
from ingestion.cid import CANCER_GROUPS, cancer_group, is_cancer, is_ill_defined
from ingestion.geo import ALL_UFS
from ingestion.suppression import suppress_small_counts


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def build_synthetic_micro_mock(
    *,
    seed: int = 42,
    years: tuple[int, ...] = (2019, 2020, 2021),
    ufs: tuple[str, ...] = ("AC", "SP", "RJ", "BA", "RS"),
    n_rows: int = 4000,
) -> pd.DataFrame:
    """
    Microdados sintéticos apenas para exercitar agregação/CID nos testes/demo.

    Não contém PII nem registros reais do SIM.
    """
    rng = _rng(seed)
    cancer_cids = [
        "C16",
        "C18",
        "C34",
        "C50",
        "C53",
        "C61",
        "C22",
        "C25",
        "C67",
        "C73",
        "C91",
        "C43",
        "C15",
        "C00",
        "C71",
    ]
    other_cids = ["R99", "R54", "R96", "I21", "J18"]
    all_cids = cancer_cids * 10 + other_cids

    # Concentra idades adultas para reduzir dispersão excessiva
    ages = list(range(40, 85))
    rows = {
        "year": rng.choice(years, size=n_rows),
        "uf": rng.choice(ufs, size=n_rows, p=[0.05, 0.45, 0.2, 0.15, 0.15]),
        "sexo": rng.choice(["M", "F"], size=n_rows, p=[0.52, 0.48]),
        "idade_anos": rng.choice(ages, size=n_rows),
        "causabas": rng.choice(all_cids, size=n_rows),
        "codmunres": "355030",
    }
    df = pd.DataFrame(rows)
    df["age_group"] = df["idade_anos"].map(age_to_group)
    return df


def build_aggregated_sample(
    *,
    seed: int = 42,
    years: tuple[int, ...] = (2019, 2020, 2021),
    ufs: tuple[str, ...] = ("AC", "SP", "RJ", "BA", "RS"),
) -> pd.DataFrame:
    """
    Contagens agregadas sintéticas com densidade suficiente para demo.

    A maioria das células fica >= 5; algumas < 5 exercitam a supressão.
    """
    rng = _rng(seed + 1)
    groups = [g.code for g in CANCER_GROUPS]
    # Faixas etárias mais relevantes para câncer
    age_groups = [g for g in AGE_GROUPS if g not in {"00-04", "05-09", "10-14", "ignorado"}]
    records: list[dict[str, Any]] = []
    for year in years:
        for uf in ufs:
            scale = {"AC": 0.3, "SP": 2.5, "RJ": 1.4, "BA": 1.0, "RS": 1.1}[uf]
            for sexo in ("M", "F"):
                for age_group in age_groups:
                    for group in groups:
                        # Base por tipo (próstata/mama/pulmão mais frequentes)
                        boost = {
                            "prostate": 2.0 if sexo == "M" else 0.05,
                            "breast": 2.2 if sexo == "F" else 0.05,
                            "lung": 1.8,
                            "colorectal": 1.5,
                            "stomach": 1.2,
                            "cervix": 1.3 if sexo == "F" else 0.0,
                            "other_cancer": 1.1,
                        }.get(group, 0.7)
                        if boost <= 0:
                            continue
                        mean = max(0.5, 6.0 * scale * boost)
                        deaths = int(rng.poisson(mean))
                        # Injeta algumas células pequenas de propósito
                        if rng.random() < 0.08:
                            deaths = int(rng.integers(1, 5))
                        if deaths <= 0:
                            continue
                        records.append(
                            {
                                "year": year,
                                "uf": uf,
                                "sexo": sexo,
                                "age_group": age_group,
                                "cancer_group": group,
                                "deaths": deaths,
                            }
                        )
    agg = pd.DataFrame.from_records(records)
    return suppress_small_counts(agg, count_col="deaths", threshold=5)


def build_population_sample(
    *,
    seed: int = 42,
    years: tuple[int, ...] = (2019, 2020, 2021, 2030),
    ufs: tuple[str, ...] = ("AC", "SP", "RJ", "BA", "RS"),
) -> pd.DataFrame:
    """Recorte sintético de população por UF/sexo/idade (escala plausível)."""
    rng = _rng(seed)
    records: list[dict[str, Any]] = []
    base_pop = {"AC": 8_000, "SP": 90_000, "RJ": 40_000, "BA": 30_000, "RS": 25_000}
    for year in years:
        for uf in ufs:
            for sexo in ("M", "F"):
                for age in range(0, 91):
                    weight = max(0.2, 1.0 - age / 120)
                    pop = int(base_pop[uf] * weight * rng.uniform(0.9, 1.1))
                    records.append(
                        {
                            "year": year,
                            "uf": uf,
                            "sexo": sexo,
                            "age": age,
                            "population": pop,
                        }
                    )
    return pd.DataFrame.from_records(records)


def write_sample_bundle(output_dir: Path, *, seed: int = 42) -> dict[str, str]:
    """Escreve o pacote mínimo versionado em data/sample/."""
    output_dir.mkdir(parents=True, exist_ok=True)

    micro = build_synthetic_micro_mock(seed=seed)
    micro = micro.copy()
    micro["is_cancer"] = micro["causabas"].map(is_cancer)
    micro["is_ill_defined"] = micro["causabas"].map(is_ill_defined)
    micro["cancer_group"] = micro["causabas"].map(cancer_group)

    cancer = micro.loc[micro["is_cancer"]].copy()
    ill = micro.loc[micro["is_ill_defined"]].copy()

    # Agregado commitado: gerado com densidade controlada (não o micro esparso)
    agg = build_aggregated_sample(seed=seed)
    # Micro ainda serve para re-agregar no demo (exercita a lógica)
    _ = aggregate_cancer_deaths(cancer, threshold=5, apply_suppression=True)

    ill_counts = (
        ill.groupby(["year", "uf", "sexo", "age_group"], as_index=False)
        .size()
        .rename(columns={"size": "deaths_ill_defined"})
        if not ill.empty
        else pd.DataFrame(columns=["year", "uf", "sexo", "age_group", "deaths_ill_defined"])
    )
    pop = build_population_sample(seed=seed)

    paths = {
        "cancer_deaths_agg": output_dir / "cancer_deaths_agg.parquet",
        "ill_defined_counts": output_dir / "ill_defined_counts.parquet",
        "ibge_population_sample": output_dir / "ibge_population_sample.parquet",
        "cancer_deaths_micro_mock": output_dir / "cancer_deaths_micro_mock.parquet",
    }
    agg.to_parquet(paths["cancer_deaths_agg"], index=False)
    ill_counts.to_parquet(paths["ill_defined_counts"], index=False)
    pop.to_parquet(paths["ibge_population_sample"], index=False)
    micro_out = micro.loc[
        :,
        ["year", "uf", "sexo", "idade_anos", "age_group", "causabas", "codmunres"],
    ]
    micro_out.to_parquet(paths["cancer_deaths_micro_mock"], index=False)

    readme = output_dir / "README.md"
    readme.write_text(
        "# Amostras (sem microdados reais)\n\n"
        "- `cancer_deaths_agg.parquet`: contagens por UF × sexo × faixa etária × "
        "grupo de câncer × ano, com células < 5 suprimidas.\n"
        "- `ill_defined_counts.parquet`: contagens de causas R00–R99.\n"
        "- `ibge_population_sample.parquet`: recorte sintético de população.\n"
        "- `cancer_deaths_micro_mock.parquet`: microdados **sintéticos** para testes "
        "(não são registros do SIM).\n\n"
        "Nenhum arquivo aqui contém PII ou microdados reais do DATASUS.\n",
        encoding="utf-8",
    )

    _ = ALL_UFS  # documenta UFs disponíveis no projeto

    return {k: str(v) for k, v in paths.items()}
