"""Filtros e agrupamentos CID-10 (neoplasias malignas e causas mal definidas)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# CID-10 Capítulo II — Neoplasias (C00–C97); exclui D00–D48 (in situ/benignas).
CANCER_CID_PREFIX = "C"
CANCER_CODE_MIN = "C00"
CANCER_CODE_MAX = "C97"

# Causas mal definidas / sintomas (Capítulo XVIII) — acompanhamento de qualidade.
ILL_DEFINED_MIN = "R00"
ILL_DEFINED_MAX = "R99"

_CID_RE = re.compile(r"^([A-Z])(\d{2})")


@dataclass(frozen=True, slots=True)
class CancerGroup:
    """Grupo analítico de neoplasias malignas (aprox. categorias GLOBOCAN/IARC)."""

    code: str
    label_pt: str
    start: str
    end: str


# Ordem importa: faixas mais específicas primeiro; residual cobre o restante C00–C97.
CANCER_GROUPS: tuple[CancerGroup, ...] = (
    CancerGroup("oral_pharynx", "Lábio, cavidade oral e faringe", "C00", "C14"),
    CancerGroup("esophagus", "Esôfago", "C15", "C15"),
    CancerGroup("stomach", "Estômago", "C16", "C16"),
    CancerGroup("colorectal", "Cólon, reto e ânus", "C18", "C21"),
    CancerGroup("liver", "Fígado e vias biliares intra-hepáticas", "C22", "C22"),
    CancerGroup("pancreas", "Pâncreas", "C25", "C25"),
    CancerGroup("lung", "Traqueia, brônquios e pulmão", "C33", "C34"),
    CancerGroup("melanoma", "Melanoma maligno da pele", "C43", "C43"),
    CancerGroup("breast", "Mama", "C50", "C50"),
    CancerGroup("cervix", "Colo do útero", "C53", "C53"),
    CancerGroup("uterus", "Corpo do útero e útero NE", "C54", "C55"),
    CancerGroup("ovary", "Ovário", "C56", "C56"),
    CancerGroup("prostate", "Próstata", "C61", "C61"),
    CancerGroup("bladder", "Bexiga", "C67", "C67"),
    CancerGroup("cns", "Meninges, encéfalo e SNC", "C70", "C72"),
    CancerGroup("thyroid", "Tireoide", "C73", "C73"),
    CancerGroup("lymphoma_leukemia", "Linfomas e leucemias", "C81", "C96"),
    CancerGroup("other_cancer", "Outras neoplasias malignas (C00–C97)", "C00", "C97"),
)


def normalize_cid(code: str | None) -> str | None:
    """Normaliza código CID-10 (maiúsculas, sem pontos; categoria de 3 chars)."""
    if code is None:
        return None
    text = str(code).strip().upper().replace(".", "")
    if not text:
        return None
    match = _CID_RE.match(text)
    if not match:
        return None
    return f"{match.group(1)}{match.group(2)}"


def _in_range(code: str, start: str, end: str) -> bool:
    return start <= code <= end


def is_cancer(code: str | None) -> bool:
    """Retorna True se a causa básica for neoplasia maligna C00–C97."""
    cid = normalize_cid(code)
    if cid is None or not cid.startswith(CANCER_CID_PREFIX):
        return False
    return _in_range(cid, CANCER_CODE_MIN, CANCER_CODE_MAX)


def is_ill_defined(code: str | None) -> bool:
    """Retorna True se a causa básica for mal definida (R00–R99)."""
    cid = normalize_cid(code)
    if cid is None:
        return False
    return _in_range(cid, ILL_DEFINED_MIN, ILL_DEFINED_MAX)


def cancer_group(code: str | None) -> str | None:
    """Mapeia CID-10 C00–C97 para o código do grupo analítico; None se não for câncer."""
    cid = normalize_cid(code)
    if cid is None or not is_cancer(cid):
        return None
    for group in CANCER_GROUPS:
        if group.code == "other_cancer":
            continue
        if _in_range(cid, group.start, group.end):
            return group.code
    return "other_cancer"


def cancer_group_label(group_code: str) -> str:
    """Rótulo em português do grupo analítico."""
    for group in CANCER_GROUPS:
        if group.code == group_code:
            return group.label_pt
    return group_code
