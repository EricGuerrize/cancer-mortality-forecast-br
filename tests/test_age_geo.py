"""Testes de idade SIM e geo UF."""

from __future__ import annotations

import pytest
from ingestion.age import age_to_group, decode_sim_age, normalize_sex
from ingestion.geo import is_valid_uf, uf_from_codmun


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("410", 10),
        ("450", 50),
        ("400", 0),
        ("505", 105),
        ("205", 0),  # dias → <1 ano
        ("999", None),
        (None, None),
        ("45", 45),  # já em anos
    ],
)
def test_decode_sim_age(raw: object, expected: int | None) -> None:
    assert decode_sim_age(raw) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("age", "group"),
    [
        (0, "00-04"),
        (4, "00-04"),
        (5, "05-09"),
        (47, "45-49"),
        (84, "80-84"),
        (85, "85+"),
        (100, "85+"),
        (None, "ignorado"),
    ],
)
def test_age_to_group(age: int | None, group: str) -> None:
    assert age_to_group(age) == group


@pytest.mark.parametrize(
    ("sexo", "expected"),
    [
        (1, "M"),
        ("2", "F"),
        ("M", "M"),
        ("Homens", "M"),
        ("Mulheres", "F"),
        (0, "I"),
        (None, "I"),
    ],
)
def test_normalize_sex(sexo: object, expected: str) -> None:
    assert normalize_sex(sexo) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("codmun", "uf"),
    [
        ("355030", "SP"),
        (3304557, "RJ"),
        ("120040", "AC"),
        ("12", "AC"),  # prefixo UF de 2 dígitos
        ("1", None),
        (None, None),
    ],
)
def test_uf_from_codmun(codmun: object, uf: str | None) -> None:
    assert uf_from_codmun(codmun) == uf  # type: ignore[arg-type]


def test_is_valid_uf() -> None:
    assert is_valid_uf("SP")
    assert not is_valid_uf("XX")
