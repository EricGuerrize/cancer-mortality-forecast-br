# Amostras versionadas (`data/sample/`)

| Arquivo | Natureza | Conteúdo |
|---------|----------|----------|
| `cancer_deaths_agg.parquet` | **Agregados reais** (SIM/DATASUS) | Óbitos por câncer (CID-10 C00–C97) × UF × sexo × faixa etária × grupo × ano. UFs **AC, SP, RJ**; anos **2020–2022**. Células com **&lt; 5** óbitos suprimidas. |
| `ill_defined_counts.parquet` | **Agregados reais** (SIM/DATASUS) | Contagens de causas mal definidas (R00–R99), mesmas UFs/anos. |
| `ibge_population_sample.parquet` | **Recorte real** (IBGE rev. 2024) | População por UF/sexo/idade; UFs AC/SP/RJ; anos 2020–2022 e 2030. Fonte: `projecoes_2024_tab1_idade_simples.xlsx`. |
| `cancer_deaths_micro_mock.parquet` | **Sintético** | Apenas para exercitar re-agregação nos testes/demo. **Não** são microdados do SIM. |

**Não há microdados reais nem PII neste diretório.** Microdados brutos ficam só em `data/raw/` (gitignored).

Citação: Ministério da Saúde/DATASUS (SIM); IBGE (Projeções da População, revisão 2024).
