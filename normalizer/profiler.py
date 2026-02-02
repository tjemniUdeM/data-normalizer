from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd
import warnings


@dataclass
class ColumnProfile:
    name: str
    inferred_type: str
    missing_pct: float
    unique_count: int
    samples: List[str]


BOOL_TRUE = {"true", "yes", "1", "y", "t","oui"}
BOOL_FALSE = {"false", "no", "0", "n", "f","non"}


def _looks_boolean(series: pd.Series) -> bool:
    values = (
        series.dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .unique()
    )
    if len(values) == 0:
        return False
    return all(v in BOOL_TRUE.union(BOOL_FALSE) for v in values)


def _looks_integer(series: pd.Series) -> bool:
    try:
        series.dropna().astype(str).str.strip().astype(int)
        return True
    except Exception:
        return False


def _looks_float(series: pd.Series) -> bool:
    try:
        series.dropna().astype(str).str.strip().astype(float)
        return True
    except Exception:
        return False


def _looks_date(series: pd.Series) -> bool:
    try:
        s = (
            series.dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA) ##we can ignore white spaces or null charaacters
            .dropna()
        )
        if s.empty:
            return False

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed = pd.to_datetime(s, errors="coerce")
        return parsed.notna().mean() >= 0.8
    except Exception:
        return False



def infer_type(series: pd.Series) -> str:
    if _looks_boolean(series):
        return "boolean"
    if _looks_integer(series):
        return "integer"
    if _looks_float(series):
        return "float"
    if _looks_date(series):
        return "date"
    return "string"


def profile_dataframe(df: pd.DataFrame, sample_size: int = 3) -> list[ColumnProfile]:
    profiles: list[ColumnProfile] = []

    total_rows = len(df)

    for col in df.columns:
        series = df[col]

        missing_pct = series.isna().mean() * 100
        unique_count = series.nunique(dropna=True)

        inferred = infer_type(series)

        samples = (
            series.dropna()
            .astype(str)
            .head(sample_size)
            .tolist()
        )

        profiles.append(
            ColumnProfile(
                name=str(col),
                inferred_type=inferred,
                missing_pct=round(missing_pct, 2),
                unique_count=int(unique_count),
                samples=samples,
            )
        )

    return profiles
