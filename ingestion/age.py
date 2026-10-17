"""Decodificação de idade SIM e faixas etárias quinquenais."""

from __future__ import annotations

from typing import Literal

AgeGroup = str

# Faixas alinhadas à população-padrão OMS (para taxas padronizadas na semana 2).
AGE_GROUPS: tuple[AgeGroup, ...] = (
    "00-04",
    "05-09",
    "10-14",
    "15-19",
    "20-24",
    "25-29",
    "30-34",
    "35-39",
    "40-44",
    "45-49",
    "50-54",
    "55-59",
    "60-64",
    "65-69",
    "70-74",
    "75-79",
    "80-84",
    "85+",
    "ignorado",
)


def decode_sim_age(idade: str | int | float | None) -> int | None:
    """
    Decodifica o campo IDADE do SIM.

    Formato clássico (3 dígitos): UQQ
    - U=1 minutos, 2 horas, 3 dias/meses (varia por dicionário), 4 anos, 5 >100 anos
    - QQ = quantidade

    Retorna idade em anos completos, ou None se ignorada/inválida.
    Idades < 1 ano retornam 0.
    """
    if idade is None:
        return None
    text = str(idade).strip()
    if not text or text in {"999", "9999", "0", "000"}:
        # "000" = ignorada em alguns layouts; "400" = <1 ano
        if text == "400":
            return 0
        if text in {"999", "9999", "0", "000"}:
            return None
    # Aceita inteiro puro (já em anos) vindo de mocks/parquet enriquecido
    if text.isdigit() and len(text) <= 2:
        return int(text)
    if not text.isdigit():
        try:
            value = int(float(text))
        except ValueError:
            return None
        return value if 0 <= value <= 120 else None

    padded = text.zfill(3)[-3:]
    unit = int(padded[0])
    qty = int(padded[1:])

    if unit == 0:
        return None
    if unit in {1, 2, 3}:  # minutos, horas, dias/meses → < 1 ano
        return 0
    if unit == 4:
        return qty
    if unit == 5:
        return 100 + qty
    return None


def age_to_group(age_years: int | float | None) -> AgeGroup:
    """Converte idade em anos para faixa quinquenal."""
    if age_years is None:
        return "ignorado"
    try:
        # pandas pode entregar float (NaN) após Series.map
        if age_years != age_years:  # NaN
            return "ignorado"
        age_int = int(age_years)
    except (TypeError, ValueError):
        return "ignorado"
    if age_int < 0:
        return "ignorado"
    if age_int >= 85:
        return "85+"
    lower = (age_int // 5) * 5
    upper = lower + 4
    return f"{lower:02d}-{upper:02d}"


SexCode = Literal["M", "F", "I"]


def normalize_sex(sexo: str | int | None) -> SexCode:
    """Normaliza SEXO do SIM para M/F/I."""
    if sexo is None:
        return "I"
    text = str(sexo).strip().upper()
    if text in {"1", "M", "MASCULINO", "HOMENS", "HOMEM"}:
        return "M"
    if text in {"2", "F", "FEMININO", "MULHERES", "MULHER"}:
        return "F"
    return "I"
