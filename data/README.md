# Dados

| Caminho | Versionado? | Conteúdo |
|---------|-------------|----------|
| `sample/` | sim | Agregados sintéticos / sem PII para `make demo` e CI |
| `raw/` | **não** (gitignored) | Downloads SIM/IBGE (`make ingest`) |

Nunca versione microdados do SIM nem arquivos `.env`.
