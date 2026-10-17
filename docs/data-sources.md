# Fontes de dados

## DATASUS — SIM (Sistema de Informações sobre Mortalidade)

- **O que é:** microdados de Declaração de Óbito (DO), causa básica em CID-10.
- **Acesso:** FTP DATASUS (`ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/`) e espelho Parquet via [PySUS](https://github.com/AlertaDengue/PySUS) (`pysus.ftp.sim`, `source="catalog"` por padrão).
- **Recorte deste projeto:** neoplasias malignas **C00–C97**; acompanhamento de causas mal definidas **R00–R99**.
- **Colunas usadas:** `CAUSABAS`, `SEXO`, `IDADE`, `DTOBITO`, `CODMUNRES`.
- **Citação:** Ministério da Saúde / DATASUS — Sistema de Informações sobre Mortalidade (SIM).

> **Licença:** PySUS é GPL-3.0 e é usado **apenas como dependência opcional** de download (`pip install '.[sim]'`). O código deste repositório permanece MIT.

## IBGE — Projeções da População (revisão 2024)

- **Arquivo verificado:** `projecoes_2024_tab1_idade_simples.xlsx`
- **URL FTP:** https://ftp.ibge.gov.br/Projecao_da_Populacao/Projecao_da_Populacao_2024/
- **Conteúdo:** população por sexo (Homens/Mulheres/Ambos) e idade simples (0–90), Brasil e UFs, anos **2000–2070**, referência 1º de julho.
- **Layout:** uma planilha (`1) POP_IDADE SIMPLES`); colunas `IDADE`, `SEXO`, `CÓD.`, `SIGLA`, `LOCAL`, depois uma coluna por ano.
- **Citação:** IBGE. Projeções da população: Brasil e Unidades da Federação: revisão 2024.

## Ética / LGPD

Trabalhamos apenas com **dados públicos agregados** em artefatos versionados (`data/sample/`). Microdados brutos do SIM, quando baixados, ficam em `data/raw/` (gitignored). As previsões são de **nível populacional**, não de risco individual.
