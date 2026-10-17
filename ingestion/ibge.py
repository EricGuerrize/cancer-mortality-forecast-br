"""Ingestão das projeções populacionais IBGE (revisão 2024)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from ingestion.age import normalize_sex
from ingestion.config import get_settings
from ingestion.geo import ALL_UFS, IBGE_REGION_SIGLAS
from ingestion.schemas import IBGE_POP_COLUMNS, assert_columns, validate_ibge_pop

logger = logging.getLogger(__name__)

DEFAULT_URL = (
    "https://ftp.ibge.gov.br/Projecao_da_Populacao/"
    "Projecao_da_Populacao_2024/projecoes_2024_tab1_idade_simples.xlsx"
)


class IbgeDownloadError(RuntimeError):
    """Falha ao baixar/parsear projeções IBGE."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30), reraise=True)
def download_ibge_xlsx(url: str, dest: Path, *, timeout: float = 120.0) -> Path:
    """Baixa o XLSX de população por sexo e idade simples."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Baixando IBGE: %s", url)
    with httpx.stream("GET", url, follow_redirects=True, timeout=timeout) as resp:
        resp.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in resp.iter_bytes():
                fh.write(chunk)
    if dest.stat().st_size < 1000:
        raise IbgeDownloadError(f"Arquivo IBGE suspeito (muito pequeno): {dest}")
    return dest


def _detect_header_row(path: Path) -> int:
    """Localiza a linha de cabeçalho (IDADE, SEXO, CÓD., SIGLA, LOCAL, anos...)."""
    preview = pd.read_excel(path, header=None, nrows=20, engine="openpyxl")
    for idx, row in preview.iterrows():
        values = [str(v).strip().upper() if pd.notna(v) else "" for v in row.tolist()]
        if "IDADE" in values and "SEXO" in values and "SIGLA" in values:
            return int(idx)
    raise IbgeDownloadError("Não foi possível localizar o cabeçalho IDADE/SEXO/SIGLA no XLSX IBGE")


def parse_ibge_population_xlsx(path: Path, *, ufs_only: bool = True) -> pd.DataFrame:
    """
    Lê `projecoes_2024_tab1_idade_simples.xlsx` e retorna formato longo.

    Fonte verificada (FTP IBGE, revisão 2024):
    - 1 planilha: "1) POP_IDADE SIMPLES"
    - Colunas: IDADE, SEXO, CÓD., SIGLA, LOCAL, 2000..2070
    - SEXO: Ambos / Homens / Mulheres
    - SIGLA: UFs + BR + grandes regiões (NO, ND, CO, SD, SU)
    - IDADE: 0..90 (90 = 90 anos ou mais na prática da tabela)
    """
    header_row = _detect_header_row(path)
    raw = pd.read_excel(path, header=header_row, engine="openpyxl")
    raw.columns = [str(c).strip() for c in raw.columns]

    required = {"IDADE", "SEXO", "SIGLA"}
    missing = required - set(raw.columns)
    if missing:
        raise IbgeDownloadError(f"Colunas IBGE ausentes: {sorted(missing)}")

    year_cols = [c for c in raw.columns if str(c).isdigit()]
    if not year_cols:
        raise IbgeDownloadError("Nenhuma coluna de ano encontrada no XLSX IBGE")

    long = raw.melt(
        id_vars=["IDADE", "SEXO", "SIGLA"],
        value_vars=year_cols,
        var_name="year",
        value_name="population",
    )
    long = long.rename(columns={"IDADE": "age", "SEXO": "sexo_raw", "SIGLA": "uf"})
    long["year"] = long["year"].astype(int)
    long["age"] = pd.to_numeric(long["age"], errors="coerce").astype("Int64")
    long["population"] = (
        pd.to_numeric(long["population"], errors="coerce").fillna(0).astype("int64")
    )
    long["uf"] = long["uf"].astype(str).str.upper().str.strip()
    long["sexo"] = long["sexo_raw"].map(normalize_sex)

    # Mantém apenas Homens/Mulheres (exclui "Ambos" para evitar dupla contagem).
    long = long.loc[long["sexo"].isin(["M", "F"])].copy()

    if ufs_only:
        long = long.loc[~long["uf"].isin(IBGE_REGION_SIGLAS)].copy()
        long = long.loc[long["uf"].isin(ALL_UFS)].copy()

    out = long.loc[:, list(IBGE_POP_COLUMNS)].reset_index(drop=True)
    assert_columns(out, IBGE_POP_COLUMNS, "ibge_pop")
    return validate_ibge_pop(out)


def ingest_ibge(
    *,
    output_dir: Path,
    url: str | None = None,
    keep_xlsx: bool = True,
) -> dict[str, Any]:
    """Baixa, parseia e grava população IBGE em Parquet particionado por year=."""
    settings = get_settings()
    url = url or settings.ibge_xlsx_url or DEFAULT_URL
    output_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = output_dir / "projecoes_2024_tab1_idade_simples.xlsx"

    try:
        download_ibge_xlsx(url, xlsx_path)
    except Exception as exc:  # noqa: BLE001
        raise IbgeDownloadError(f"Falha no download IBGE: {exc}") from exc

    df = parse_ibge_population_xlsx(xlsx_path)
    pop_dir = output_dir / "ibge_population"
    written: list[Path] = []
    for year, part in df.groupby("year"):
        part_dir = pop_dir / f"year={int(year)}"
        part_dir.mkdir(parents=True, exist_ok=True)
        path = part_dir / "part-0.parquet"
        part.to_parquet(path, index=False)
        written.append(path)

    # Também grava um arquivo único conveniente para demos pequenas.
    single = output_dir / "ibge_population.parquet"
    df.to_parquet(single, index=False)

    if not keep_xlsx and xlsx_path.exists():
        xlsx_path.unlink()

    return {
        "rows": int(len(df)),
        "years": sorted(df["year"].unique().tolist()),
        "ufs": sorted(df["uf"].unique().tolist()),
        "parquet": str(single),
        "partitions": [str(p) for p in written],
        "xlsx": str(xlsx_path) if xlsx_path.exists() else None,
    }
