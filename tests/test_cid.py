"""Testes de filtro e agrupamento CID-10."""

from __future__ import annotations

import pytest
from ingestion.cid import (
    cancer_group,
    cancer_group_label,
    is_cancer,
    is_ill_defined,
    normalize_cid,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("c34", "C34"),
        ("C34.1", "C34"),
        ("C509", "C50"),
        ("R99", "R99"),
        ("", None),
        (None, None),
        ("ZZZ", None),
    ],
)
def test_normalize_cid(raw: str | None, expected: str | None) -> None:
    assert normalize_cid(raw) == expected


@pytest.mark.parametrize(
    ("code", "cancer", "ill"),
    [
        ("C00", True, False),
        ("C50", True, False),
        ("C97", True, False),
        ("C98", False, False),  # fora de C00–C97
        ("D05", False, False),
        ("R00", False, True),
        ("R99", False, True),
        ("I21", False, False),
        (None, False, False),
    ],
)
def test_is_cancer_and_ill_defined(code: str | None, cancer: bool, ill: bool) -> None:
    assert is_cancer(code) is cancer
    assert is_ill_defined(code) is ill


@pytest.mark.parametrize(
    ("code", "group"),
    [
        ("C16", "stomach"),
        ("C18", "colorectal"),
        ("C20", "colorectal"),
        ("C34", "lung"),
        ("C50", "breast"),
        ("C53", "cervix"),
        ("C61", "prostate"),
        ("C81", "lymphoma_leukemia"),
        ("C91", "lymphoma_leukemia"),
        ("C17", "other_cancer"),  # intestino delgado → residual
        ("I21", None),
    ],
)
def test_cancer_group(code: str, group: str | None) -> None:
    assert cancer_group(code) == group


def test_cancer_group_label() -> None:
    assert "Mama" in cancer_group_label("breast")
    assert cancer_group_label("desconhecido") == "desconhecido"
