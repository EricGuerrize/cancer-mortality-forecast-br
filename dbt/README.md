# dbt-duckdb — semana 2

Transformações analíticas sobre os agregados SIM/IBGE: **staging → intermediate → marts**,
com testes de qualidade e seeds (população-padrão OMS + rótulos CID).

## Por que dbt-duckdb?

Roda **100% local** (sem conta Snowflake/BigQuery/Redshift). O mesmo projeto troca o
`profiles.yml` para um warehouse em nuvem depois — padrão comum em healthtech.

## Linhagem

```text
sources (Parquet sample)
  ├─ cancer_deaths_agg ──► stg_sim_cancer_deaths ──► int_cancer_deaths_labeled
  │                                                      │
  │                                                      ▼
  │                                            int_deaths_with_population
  │                                                      │
  ├─ ibge_population_sample ──► stg_ibge_population      │
  │                                   │                  │
  │                                   ▼                  │
  │                         int_population_age_group ────┤
  │                                                      ▼
  │                              ┌── fct_crude_mortality_rates
  │                              ├── fct_age_standardized_rates  (+ seed WHO)
  │                              └── dim_cancer_groups           (+ seed labels)
  │
  └─ ill_defined_counts ──► stg_sim_ill_defined ──► fct_ill_defined_quality
```

## Camadas

| Camada | Modelos | Papel |
|--------|---------|-------|
| **staging** | `stg_sim_cancer_deaths`, `stg_sim_ill_defined`, `stg_ibge_population` | Tipagem/normalização dos Parquets |
| **intermediate** | `int_population_age_group`, `int_cancer_deaths_labeled`, `int_deaths_with_population` | Faixas etárias, rótulos CID, join óbitos×pop |
| **marts** | `dim_cancer_groups`, `fct_crude_mortality_rates`, `fct_age_standardized_rates`, `fct_ill_defined_quality` | Taxas brutas, ASR (OMS), qualidade R00–R99 |

## Testes

- Genéricos: `not_null`, `unique`, `accepted_values`, `relationships`, `dbt_utils.unique_combination_of_columns`
- Customizado (macro): `deaths_null_when_suppressed` — células suprimidas não podem ter `deaths` preenchido
- Singulares: pesos OMS = 100 000; taxas brutas/ASR ≥ 0

## Como rodar

Na raiz do repositório:

```bash
pip install -e ".[dbt]"
make dbt-deps
make dbt-build
```

Equivalente:

```bash
cd dbt
dbt deps --profiles-dir .
dbt build --profiles-dir .
```

Artefato DuckDB: `data/processed/cancer_mortality.duckdb` (gitignored).

No CI usa-se `--target ci` (DuckDB in-memory) com a mesma amostra em `data/sample/`.
