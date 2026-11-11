"""Mapeamento município IBGE → UF e lista de UFs válidas."""

from __future__ import annotations

UF_CODES: dict[str, str] = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}

ALL_UFS: tuple[str, ...] = tuple(sorted(UF_CODES.values()))

# No XLSX IBGE revisão 2024, regiões usam NO, ND, CO, SD, SU e BR (SE = Sergipe/UF).
IBGE_REGION_SIGLAS = frozenset({"BR", "NO", "ND", "CO", "SD", "SU"})


def uf_from_codmun(codmun: str | int | None) -> str | None:
    """Extrai UF a partir do código IBGE do município (6 ou 7 dígitos)."""
    if codmun is None:
        return None
    text = str(codmun).strip()
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) < 2:
        return None
    return UF_CODES.get(digits[:2])


def is_valid_uf(uf: str) -> bool:
    return uf.upper() in ALL_UFS
