# Forecasting

Na **semana 2** há apenas um baseline **naive** (`naive.py`): copia a última ASR
observada até 2030. Serve de etapa no orquestrador (Dagster) até a semana 3
(ETS/ARIMA, Poisson/NegBin, LightGBM, backtesting, MLflow).

```bash
# após make dbt-build
python -c "from forecasting.naive import run_naive_forecast; print(run_naive_forecast())"
```

Saída: `data/processed/naive_forecast.parquet`.
