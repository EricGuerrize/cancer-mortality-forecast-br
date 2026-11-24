.PHONY: setup lint test ingest demo sample docker-build docker-demo \
	dbt-deps dbt-build dbt-docs dagster dagster-job clean help

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
CLI ?= $(PYTHON) -m ingestion.cli
DBT ?= dbt
DBT_DIR ?= dbt

help:
	@echo "Alvos disponíveis:"
	@echo "  make setup         - instala o pacote + extras de desenvolvimento"
	@echo "  make lint          - ruff check"
	@echo "  make test          - pytest"
	@echo "  make sample        - gera data/sample/ sintético (testes)"
	@echo "  make sample-real   - regenera data/sample/ com agregados reais (rede)"
	@echo "  make demo          - roda demo offline a partir de data/sample/"
	@echo "  make ingest        - download completo SIM + IBGE → data/raw/"
	@echo "  make dbt-deps      - instala pacotes dbt (dbt_utils)"
	@echo "  make dbt-build     - dbt build (sample → DuckDB)"
	@echo "  make dbt-docs      - gera e serve documentação dbt"
	@echo "  make dagster       - sobe UI Dagster (localhost:3000)"
	@echo "  make dagster-job   - executa o job completo via CLI"
	@echo "  make docker-build  - build da imagem Docker"
	@echo "  make docker-demo   - demo via docker compose"
	@echo "  make clean         - remove artefatos locais"

setup:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev,orchestration]"

lint:
	$(PYTHON) -m ruff check ingestion forecasting orchestration tests
	$(PYTHON) -m ruff format --check ingestion forecasting orchestration tests

test:
	$(PYTHON) -m pytest

sample:
	$(CLI) make-sample

sample-real:
	$(PIP) install -e ".[dev,sim]"
	$(CLI) make-sample-real --years 2020-2022 --ufs AC,SP,RJ

demo:
	$(CLI) demo

# Download completo (requer rede + extras [sim]).
ingest:
	$(PIP) install -e ".[dev,sim]"
	$(CLI) ingest-ibge
	$(CLI) ingest-sim --years 2018-2022

dbt-deps:
	$(PIP) install -e ".[dbt]"
	cd $(DBT_DIR) && $(DBT) deps --profiles-dir .

dbt-build: dbt-deps
	mkdir -p data/processed
	cd $(DBT_DIR) && $(DBT) build --profiles-dir .

dbt-docs:
	cd $(DBT_DIR) && $(DBT) docs generate --profiles-dir .
	cd $(DBT_DIR) && $(DBT) docs serve --profiles-dir . --port 8080

dagster:
	$(PIP) install -e ".[orchestration]"
	dagster dev -m orchestration.definitions -h 0.0.0.0 -p 3000

dagster-job:
	$(PIP) install -e ".[orchestration]"
	dagster job execute -m orchestration.definitions -j cancer_mortality_pipeline

docker-build:
	docker build -t cancer-mortality-forecast-br:local .

docker-demo:
	docker compose run --rm demo

clean:
	rm -rf .pytest_cache .ruff_cache dist build *.egg-info
	rm -rf dbt/target dbt/dbt_packages dbt/logs
	rm -rf data/processed/*.duckdb data/processed/*.parquet data/processed/*.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
