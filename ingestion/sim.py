"""Download e transformação de óbitos SIM (DATASUS) via PySUS / fallbacks."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from ingestion.age import age_to_group, decode_sim_age, normalize_sex
from ingestion.cid import cancer_group, is_cancer, is_ill_defined
from ingestion.geo import ALL_UFS, uf_from_codmun
from ingestion.schemas import SIM_RAW_COLUMNS, assert_columns

logger = logging.getLogger(__name__)

# Colunas mínimas necessárias do microdado SIM.
SIM_KEEP_COLUMNS = ("CAUSABAS", "SEXO", "IDADE", "DTOBITO", "CODMUNRES")


class SimDownloadError(RuntimeError):
    """Falha ao obter dados SIM após retries/fallbacks."""


def _import_pysus() -> Any:
    try:
        import pysus  # noqa: WPS451 — dependência opcional GPL
    except ImportError as exc:
        raise SimDownloadError(
            "PySUS não está instalado. Instale com: pip install 'cancer-mortality-forecast-br[sim]'"
        ) from exc
    return pysus


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30), reraise=True)
def _download_sim_once(
    pysus: Any,
    *,
    state: str,
    year: int,
    source: str,
) -> pd.DataFrame:
    """Uma tentativa de download SIM para UF/ano."""
    # as_dataframe=True: PySUS 2.11+ pode devolver FileBag por padrão.
    attempts: list[dict[str, Any]] = [
        {"state": state, "year": year, "source": source, "as_dataframe": True},
        {"state": state, "year": year, "as_dataframe": True},
        {"state": state, "year": year, "source": source},
        {"state": state, "year": year},
    ]
    last_exc: Exception | None = None
    df: Any = None
    for kwargs in attempts:
        try:
            df = pysus.ftp.sim(**kwargs)
            break
        except TypeError as exc:
            last_exc = exc
            continue
    else:
        raise SimDownloadError(f"Assinatura PySUS incompatível para {state}/{year}: {last_exc}")

    if df is None:
        raise SimDownloadError(f"SIM vazio: {state}/{year} (source={source})")
    if not isinstance(df, pd.DataFrame):
        # FileBag / objeto com to_dataframe
        if hasattr(df, "to_dataframe"):
            df = df.to_dataframe()
        elif hasattr(df, "df"):
            df = df.df
        else:
            raise SimDownloadError(f"Tipo inesperado do PySUS: {type(df)}")
    if df.empty:
        logger.warning("SIM sem registros: %s/%s (source=%s)", state, year, source)
    return df


def download_sim_uf_year(
    state: str,
    year: int,
    *,
    sources: Sequence[str] = ("catalog", "origin"),
) -> pd.DataFrame:
    """
    Baixa óbitos SIM para uma UF/ano.

    Tenta primeiro o espelho Parquet (catalog); se falhar, tenta origem FTP.
    """
    pysus = _import_pysus()
    errors: list[str] = []
    for source in sources:
        try:
            logger.info("Baixando SIM %s/%s via source=%s", state, year, source)
            return _download_sim_once(pysus, state=state, year=year, source=source)
        except Exception as exc:  # noqa: BLE001 — consolidamos fallbacks
            msg = f"{source}: {exc}"
            errors.append(msg)
            logger.warning("Falha SIM %s/%s (%s)", state, year, msg)
    raise SimDownloadError(
        f"Não foi possível baixar SIM {state}/{year}. Tentativas: {'; '.join(errors)}"
    )


def _year_from_dtobito(series: pd.Series, fallback_year: int) -> pd.Series:
    """
    Extrai o ano de DTOBITO.

    O SIM usa preferencialmente `ddmmaaaa`. Datas como `19052020` (19/05/2020)
    NÃO devem ser lidas como ISO (`1905-20-20`).
    """
    text = series.astype(str).str.replace(r"\D", "", regex=True)
    mask8 = text.str.len() == 8
    y_br = pd.to_numeric(text.where(mask8).str[-4:], errors="coerce")
    y_iso = pd.to_numeric(text.where(mask8).str[:4], errors="coerce")
    # Aceita BR se o ano estiver em janela plausível do SIM CID-10; senão tenta ISO.
    br_ok = y_br.between(1996, 2100)
    years = y_br.where(br_ok, y_iso)
    years = years.fillna(fallback_year).astype(int)
    return years


def transform_sim_microdata(
    df: pd.DataFrame,
    *,
    uf: str,
    year: int,
) -> pd.DataFrame:
    """Seleciona colunas, deriva idade/UF/grupos CID e marca câncer / mal definidas."""
    if df.empty:
        return pd.DataFrame(columns=list(SIM_RAW_COLUMNS))

    cols = {c.upper(): c for c in df.columns}
    missing = [c for c in SIM_KEEP_COLUMNS if c not in cols]
    # Aceita variação de capitalização
    rename = {}
    for need in SIM_KEEP_COLUMNS:
        if need in cols:
            rename[cols[need]] = need
        else:
            # tenta casefold
            found = next((c for c in df.columns if c.upper() == need), None)
            if found:
                rename[found] = need
            else:
                missing.append(need)
    # Ainda permite subset se CAUSABAS existir
    if missing and "CAUSABAS" not in rename.values() and "CAUSABAS" not in df.columns:
        raise ValueError(f"Colunas SIM ausentes: {sorted(set(missing))}")

    work = df.rename(columns=rename)
    for col in SIM_KEEP_COLUMNS:
        if col not in work.columns:
            work[col] = pd.NA

    work = work.loc[:, list(SIM_KEEP_COLUMNS)].copy()
    work["year"] = _year_from_dtobito(work["DTOBITO"], year)
    work["uf"] = work["CODMUNRES"].map(uf_from_codmun).fillna(uf.upper())
    work["sexo"] = work["SEXO"].map(normalize_sex)
    work["idade_anos"] = work["IDADE"].map(decode_sim_age)
    work["age_group"] = work["idade_anos"].map(age_to_group)
    work["causabas"] = work["CAUSABAS"].astype(str)
    work["is_cancer"] = work["causabas"].map(is_cancer)
    work["is_ill_defined"] = work["causabas"].map(is_ill_defined)
    work["cancer_group"] = work["causabas"].map(cancer_group)
    work["codmunres"] = work["CODMUNRES"].astype(str)

    out = work.loc[:, list(SIM_RAW_COLUMNS)]
    assert_columns(out, SIM_RAW_COLUMNS, "sim_raw")
    return out


def filter_cancer_and_ill_defined(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa registros de câncer (C00–C97) e causas mal definidas (R00–R99)."""
    if df.empty:
        empty = df.copy()
        return empty, empty
    cancer = df.loc[df["is_cancer"]].copy()
    ill = df.loc[df["is_ill_defined"]].copy()
    return cancer, ill


def write_sim_partitioned(df: pd.DataFrame, output_dir: Path) -> list[Path]:
    """Escreve Parquet particionado por year= / uf=."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if df.empty:
        path = output_dir / "empty.parquet"
        df.to_parquet(path, index=False)
        return [path]

    for (year, uf), part in df.groupby(["year", "uf"], dropna=False):
        part_dir = output_dir / f"year={int(year)}" / f"uf={uf}"
        part_dir.mkdir(parents=True, exist_ok=True)
        path = part_dir / "part-0.parquet"
        part.to_parquet(path, index=False)
        written.append(path)
    return written


def ingest_sim(
    *,
    years: Iterable[int],
    ufs: Sequence[str] | None,
    output_dir: Path,
    cancer_only_partition: bool = True,
) -> dict[str, Any]:
    """
    Pipeline SIM: download → transform → filtra câncer (+ conta mal definidas) → Parquet.

    Os microdados de câncer são gravados em `output_dir/sim_cancer/`.
    Contagens de causas mal definidas vão para `output_dir/sim_ill_defined_counts.parquet`.
    """
    uf_list = list(ufs) if ufs else list(ALL_UFS)
    year_list = list(years)
    frames: list[pd.DataFrame] = []
    ill_frames: list[pd.DataFrame] = []
    failures: list[str] = []

    for year in year_list:
        for uf in uf_list:
            try:
                raw = download_sim_uf_year(uf, int(year))
                transformed = transform_sim_microdata(raw, uf=uf, year=int(year))
                cancer, ill = filter_cancer_and_ill_defined(transformed)
                if cancer_only_partition:
                    frames.append(cancer)
                else:
                    frames.append(transformed)
                if not ill.empty:
                    ill_frames.append(ill)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{uf}/{year}: {exc}")
                logger.error("Erro SIM %s/%s: %s", uf, year, exc)

    cancer_dir = output_dir / "sim_cancer"
    if frames:
        all_cancer = pd.concat(frames, ignore_index=True)
    else:
        all_cancer = pd.DataFrame(columns=list(SIM_RAW_COLUMNS))
    paths = write_sim_partitioned(all_cancer, cancer_dir)

    if ill_frames:
        ill_all = pd.concat(ill_frames, ignore_index=True)
        ill_counts = (
            ill_all.groupby(["year", "uf", "sexo", "age_group"], as_index=False)
            .size()
            .rename(columns={"size": "deaths_ill_defined"})
        )
    else:
        ill_counts = pd.DataFrame(columns=["year", "uf", "sexo", "age_group", "deaths_ill_defined"])
    ill_path = output_dir / "sim_ill_defined_counts.parquet"
    output_dir.mkdir(parents=True, exist_ok=True)
    ill_counts.to_parquet(ill_path, index=False)

    ill_total = int(ill_counts["deaths_ill_defined"].sum()) if not ill_counts.empty else 0
    return {
        "cancer_rows": int(len(all_cancer)),
        "ill_defined_rows": ill_total,
        "partitions": [str(p) for p in paths],
        "ill_defined_path": str(ill_path),
        "failures": failures,
    }
