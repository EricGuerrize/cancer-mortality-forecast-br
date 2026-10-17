# Proveniência

Gerado localmente a partir do espelho Parquet PySUS (`pysus.ftp.sim`, source=catalog)
e do FTP IBGE revisão 2024. Pipeline: download → filtro CID → agregação →
supressão de células &lt; 5 → Parquet versionado.

Comando de regeneração (rede necessária):

```bash
pip install -e ".[dev,sim]"
python -m ingestion.cli make-sample-real --ufs AC,SP,RJ --years 2020-2022
```
