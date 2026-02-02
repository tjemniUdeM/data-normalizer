from __future__ import annotations
import re
import pandas as pd
from normalizer.profiler import _looks_date


BOOL_TRUE = {"true", "yes", "1", "y", "t","oui"}
BOOL_FALSE = {"false", "no", "0", "n", "f","non"}

def _parse_month_middle_date(value: object) -> str | None:
    
    ##Parse dates where the month is always the middle token.
    ##Returns ISO 'YYYY-MM-DD' or None if not parseable.
    
    if pd.isna(value):
        return None

    s = str(value).strip()
    if not s or s.lower() in {"null", "none", "na", "n/a"}:
        return None

    parts = [p for p in re.split(r"\D+", s) if p]
    if len(parts) != 3:
        return None

    a, b, c = parts  # month is always b
    if len(a) == 4:
        year_str, month_str, day_str = a, b, c
    elif len(c) == 4:
        day_str, month_str, year_str = a, b, c
    else:
        return None

    # Validate numeric
    try:
        year = int(year_str)
        month = int(month_str)
        day = int(day_str)
    except ValueError:
        return None

    # Basic range validation
    if not (1900 <= year <= 2100):
        return None
    if not (1 <= month <= 12):
        return None
    if not (1 <= day <= 31):
        return None

    return f"{year:04d}-{month:02d}-{day:02d}"


def _normalize_date_month_middle(series: pd.Series) -> pd.Series:
    iso = series.apply(_parse_month_middle_date)
    return pd.to_datetime(iso, errors="coerce")

def _normalize_column_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^\w]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def _normalize_string(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip()
    s = s.replace({"": pd.NA, "null": pd.NA, "NULL": pd.NA})
    return s


def _normalize_boolean(series: pd.Series) -> pd.Series:
    def to_bool(val):
        if pd.isna(val):
            return pd.NA
        v = str(val).strip().lower()
        if v in BOOL_TRUE:
            return True
        if v in BOOL_FALSE:
            return False
        return pd.NA

    return series.apply(to_bool).astype("boolean")


def _normalize_integer(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .replace("", pd.NA)
        .pipe(pd.to_numeric, errors="coerce")
        .astype("Int64")
    )


def _normalize_float(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .replace("", pd.NA)
        .pipe(pd.to_numeric, errors="coerce")
        .astype("Float64")
    )


def _normalize_date(series: pd.Series) -> pd.Series:
    s = (
        series.astype("string")
        .str.strip()
        .replace({"": pd.NA, "null": pd.NA, "NULL": pd.NA})
    )
    return pd.to_datetime(s, errors="coerce")



def normalize_dataframe(df: pd.DataFrame, profiles) -> pd.DataFrame:
    df = df.copy()

    # Normalize column names
    df.columns = [_normalize_column_name(c) for c in df.columns]

    for profile in profiles:
        col = _normalize_column_name(profile.name)
        series = df[col]

        if profile.inferred_type == "boolean":
            df[col] = _normalize_boolean(series)
        elif profile.inferred_type == "integer":
            df[col] = _normalize_integer(series)
        elif profile.inferred_type == "float":
            df[col] = _normalize_float(series)
        elif profile.inferred_type == "date" or _looks_date(series):
            df[col] = _normalize_date(series)
        else:
            # Try deterministic month-middle date parsing first last chance in case it is a date and failed the panda's df check
            parsed = _normalize_date_month_middle(series)
            success_ratio = parsed.notna().mean()

            if success_ratio >= 0.8 and parsed.notna().sum() > 0:
                df[col] = parsed
            else:
                df[col] = _normalize_string(series)


    return df
