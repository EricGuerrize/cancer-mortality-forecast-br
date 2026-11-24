"""
Definições Dagster do pipeline: ingestão → dbt build → forecast naive → qualidade.

Escolha: Dagster (em vez de Airflow) para um compose enxuto (1 serviço),
assets Python nativos alinhados à linhagem dbt, e UI local sem Postgres/Redis.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

import duckdb
from dagster import (
    AssetExecutionContext,
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = REPO_ROOT / "dbt"
DUCKDB_PATH = REPO_ROOT / "data" / "processed" / "cancer_mortality.duckdb"
FORECAST_PATH = REPO_ROOT / "data" / "processed" / "naive_forecast.parquet"
QUALITY_REPORT = REPO_ROOT / "data" / "processed" / "quality_report.json"


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    logger.info("exec: %s", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(cwd or REPO_ROOT))


@asset(
    group_name="ingest",
    description="Valida a amostra pública offline (data/sample/) sem rede.",
)
def ingest_sample(context: AssetExecutionContext) -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    from ingestion.demo import run_demo

    summary = run_demo()
    context.log.info("Demo/sample OK: %s", summary)
    return summary


@asset(
    deps=[ingest_sample],
    group_name="transform",
    description="dbt build (staging → intermediate → marts) via dbt-duckdb.",
)
def dbt_build(context: AssetExecutionContext) -> dict:
    # CWD = dbt/ para que sample_data_dir=../data/sample resolva corretamente.
    (REPO_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    _run(["dbt", "deps", "--profiles-dir", "."], cwd=DBT_DIR)
    _run(["dbt", "build", "--profiles-dir", "."], cwd=DBT_DIR)
    context.log.info("dbt build concluído → %s", DUCKDB_PATH)
    return {"duckdb": str(DUCKDB_PATH), "exists": DUCKDB_PATH.exists()}


@asset(
    deps=[dbt_build],
    group_name="forecast",
    description="Baseline naive (última ASR → horizonte 2030). Placeholder da semana 3.",
)
def train_and_forecast(context: AssetExecutionContext) -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    from forecasting.naive import run_naive_forecast

    summary = run_naive_forecast(duckdb_path=DUCKDB_PATH, output_path=FORECAST_PATH)
    context.log.info("Forecast naive: %s", summary)
    return summary


@asset(
    deps=[train_and_forecast],
    group_name="quality",
    description="Checagens de qualidade pós-pipeline (ASR, R00–R99, forecast).",
)
def quality_checks(context: AssetExecutionContext) -> dict:
    if not DUCKDB_PATH.exists():
        raise FileNotFoundError(DUCKDB_PATH)

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        asr_rows = con.execute("select count(*) from marts.fct_age_standardized_rates").fetchone()[
            0
        ]
        crude_rows = con.execute("select count(*) from marts.fct_crude_mortality_rates").fetchone()[
            0
        ]
        ill_max = con.execute(
            "select max(ill_defined_share) from marts.fct_ill_defined_quality"
        ).fetchone()[0]
        neg_asr = con.execute(
            "select count(*) from marts.fct_age_standardized_rates where asr_per_100k < 0"
        ).fetchone()[0]
    finally:
        con.close()

    forecast_ok = FORECAST_PATH.exists()
    report = {
        "asr_rows": int(asr_rows),
        "crude_rows": int(crude_rows),
        "ill_defined_share_max": float(ill_max) if ill_max is not None else None,
        "negative_asr_rows": int(neg_asr),
        "forecast_exists": forecast_ok,
        "passed": bool(asr_rows > 0 and crude_rows > 0 and neg_asr == 0 and forecast_ok),
    }
    if not report["passed"]:
        raise RuntimeError(f"Quality gate falhou: {report}")

    QUALITY_REPORT.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    context.log.info("Quality OK: %s", report)
    return report


pipeline_job = define_asset_job(
    name="cancer_mortality_pipeline",
    selection=AssetSelection.groups("ingest", "transform", "forecast", "quality"),
    description="Ingestão sample → dbt build → forecast naive → quality checks",
)

daily_schedule = ScheduleDefinition(
    job=pipeline_job,
    cron_schedule="0 6 * * *",
    name="cancer_mortality_daily",
)

defs = Definitions(
    assets=[ingest_sample, dbt_build, train_and_forecast, quality_checks],
    jobs=[pipeline_job],
    schedules=[daily_schedule],
)
