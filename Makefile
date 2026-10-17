.PHONY: setup lint test ingest demo sample docker-build docker-demo clean help

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
CLI ?= $(PYTHON) -m ingestion.cli

help:
	@echo "Alvos disponíveis:"
	@echo "  make setup         - instala o pacote + extras de desenvolvimento"
	@echo "  make lint          - ruff check"
	@echo "  make test          - pytest"
	@echo "  make sample        - gera data/sample/ (agregados sintéticos)"
	@echo "  make demo          - roda demo offline a partir de data/sample/"
	@echo "  make ingest        - download completo SIM + IBGE → data/raw/"
	@echo "  make docker-build  - build da imagem Docker"
	@echo "  make docker-demo   - demo via docker compose"
	@echo "  make clean         - remove artefatos locais"

setup:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check ingestion tests
	$(PYTHON) -m ruff format --check ingestion tests

test:
	$(PYTHON) -m pytest

sample:
	$(CLI) make-sample

demo:
	$(CLI) demo

# Download completo (requer rede + extras [sim]).
ingest:
	$(PIP) install -e ".[dev,sim]"
	$(CLI) ingest-ibge
	$(CLI) ingest-sim --years 2018-2022

docker-build:
	docker build -t cancer-mortality-forecast-br:local .

docker-demo:
	docker compose run --rm demo

clean:
	rm -rf .pytest_cache .ruff_cache dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
