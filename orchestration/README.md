# Orquestração — Dagster

## Por que Dagster (e não Airflow)?

| Critério | Dagster | Airflow (LocalExecutor) |
|----------|---------|-------------------------|
| Compose local | **1 serviço** (`dagster dev`) | webserver + scheduler + Postgres (+ Redis) |
| Modelo mental | Assets = linhagem (encaixa com dbt) | Tasks/DAGs imperativos |
| Setup portfolio | minutos | mais frágil em laptop/CI |
| Exigência da vaga | Airflow **ou** Dagster | idem |

O pipeline espelha o que um DAG Airflow faria:

```text
ingest_sample → dbt_build → train_and_forecast → quality_checks
```

## Como rodar

### Opção A — UI local (sem Docker)

```bash
pip install -e ".[orchestration]"
make dagster
# UI: http://localhost:3000
# Materialize o job `cancer_mortality_pipeline`
```

### Opção B — Docker Compose

```bash
docker compose up --build dagster
# UI: http://localhost:3000
```

### Job completo via CLI

```bash
dagster job execute -m orchestration.definitions -j cancer_mortality_pipeline
```

## Assets

| Asset | Grupo | O que faz |
|-------|-------|-----------|
| `ingest_sample` | ingest | Valida `data/sample/` (demo offline) |
| `dbt_build` | transform | `dbt deps` + `dbt build` |
| `train_and_forecast` | forecast | Baseline naive → `data/processed/naive_forecast.parquet` |
| `quality_checks` | quality | Gate: marts populados, ASR ≥ 0, forecast existe |
