"""Regressão: DTOBITO ddmmaaaa não deve virar ano ISO falso (ex.: 19052020 → 1905)."""

from __future__ import annotations

import pandas as pd
from ingestion.sim import _year_from_dtobito


def test_dtobito_prefers_brazilian_day_month_year() -> None:
    s = pd.Series(
        [
            "15062020",  # 15/06/2020
            "19052020",  # 19/05/2020 — começa com 19, mas NÃO é ano 1905
            "20200519",  # ISO raro; últimos 4 = 0519 inválidos → cai no ISO 2020
            "31122021",
        ]
    )
    years = _year_from_dtobito(s, fallback_year=2099)
    assert years.tolist() == [2020, 2020, 2020, 2021]
