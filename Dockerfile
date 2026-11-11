# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY ingestion ./ingestion
COPY data/sample ./data/sample
COPY tests ./tests
COPY Makefile ./

RUN pip install --upgrade pip \
    && pip install -e ".[dev]"

# Bind services to 0.0.0.0:$PORT when API/dashboard exist (semana 4 / Render).
EXPOSE 8000

CMD ["make", "demo"]
