"""Configuração de caminhos e parâmetros de ingestão."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default=REPO_ROOT / "data")
    raw_dir: Path | None = None
    sample_dir: Path | None = None

    # SIM
    sim_years_start: int = 2010
    sim_years_end: int = 2022
    sim_ufs: str = "all"  # "all" ou lista separada por vírgula
    sim_max_retries: int = 3

    # IBGE
    ibge_xlsx_url: str = (
        "https://ftp.ibge.gov.br/Projecao_da_Populacao/"
        "Projecao_da_Populacao_2024/projecoes_2024_tab1_idade_simples.xlsx"
    )

    @property
    def raw(self) -> Path:
        return self.raw_dir or (self.data_dir / "raw")

    @property
    def sample(self) -> Path:
        return self.sample_dir or (self.data_dir / "sample")

    def parsed_ufs(self) -> list[str] | None:
        raw = self.sim_ufs.strip()
        if not raw or raw.lower() == "all":
            return None
        return [u.strip().upper() for u in raw.split(",") if u.strip()]


def get_settings() -> Settings:
    return Settings()
