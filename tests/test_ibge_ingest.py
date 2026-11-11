"""Testes de ingestão IBGE com rede e XLSX mockados."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from ingestion.age import normalize_sex
from ingestion.ibge import IbgeDownloadError, parse_ibge_population_xlsx


def _write_mini_ibge_xlsx(path: Path) -> Path:
    """Cria um XLSX mínimo no layout da revisão 2024."""
    # openpyxl via pandas
    header_rows = [
        ["Projeções das Populações, Revisão 2024", None, None, None, None, None],
        ["Brasil e UFs", None, None, None, None, None],
        [None, None, None, None, None, None],
        ["IDADE", "SEXO", "CÓD.", "SIGLA", "LOCAL", 2020],
        [0, "Homens", 35, "SP", "São Paulo", 1000],
        [0, "Mulheres", 35, "SP", "São Paulo", 1100],
        [0, "Ambos", 35, "SP", "São Paulo", 2100],
        [1, "Homens", 35, "SP", "São Paulo", 900],
        [1, "Mulheres", 35, "SP", "São Paulo", 950],
        [0, "Homens", 0, "BR", "Brasil", 5000],
        [0, "Mulheres", 0, "BR", "Brasil", 5100],
        [0, "Homens", 33, "RJ", "Rio de Janeiro", 800],
        [0, "Mulheres", 33, "RJ", "Rio de Janeiro", 820],
    ]
    df = pd.DataFrame(header_rows)
    df.to_excel(path, index=False, header=False, engine="openpyxl")
    return path


def test_parse_ibge_population_xlsx(tmp_path: Path) -> None:
    xlsx = _write_mini_ibge_xlsx(tmp_path / "mini.xlsx")
    out = parse_ibge_population_xlsx(xlsx, ufs_only=True)
    assert set(out.columns) == {"year", "uf", "sexo", "age", "population"}
    assert set(out["uf"]) == {"SP", "RJ"}
    assert set(out["sexo"]) == {"M", "F"}
    assert "BR" not in set(out["uf"])
    # Ambos excluído
    assert len(out) == 6  # SP: 4 linhas (0/1 × M/F) + RJ: 2 (0 × M/F)
    assert out["population"].sum() == 1000 + 1100 + 900 + 950 + 800 + 820


def test_normalize_sex_ibge_labels() -> None:
    assert normalize_sex("Homens") == "M"
    assert normalize_sex("Mulheres") == "F"


def test_ingest_ibge_with_mocked_download(tmp_path: Path) -> None:
    from ingestion.ibge import ingest_ibge

    xlsx = _write_mini_ibge_xlsx(tmp_path / "src.xlsx")

    def _fake_download(url: str, dest: Path, **kwargs):
        dest.write_bytes(xlsx.read_bytes())
        return dest

    with patch("ingestion.ibge.download_ibge_xlsx", side_effect=_fake_download):
        result = ingest_ibge(output_dir=tmp_path / "raw", url="https://example.invalid/x.xlsx")
    assert result["rows"] == 6
    assert Path(result["parquet"]).exists()
    loaded = pd.read_parquet(result["parquet"])
    assert len(loaded) == 6


def test_parse_missing_header_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.xlsx"
    pd.DataFrame([[1, 2], [3, 4]]).to_excel(bad, index=False, header=False, engine="openpyxl")
    with pytest.raises(IbgeDownloadError):
        parse_ibge_population_xlsx(bad)
