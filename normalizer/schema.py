from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import re

import pandas as pd


def _sql_safe_identifier(name: str) -> str:
    # basic: snake_case already, but still protect
    name = re.sub(r"[^\w]+", "_", name)
    if name and name[0].isdigit():
        name = "_" + name
    return name.lower()


def _infer_varchar_len(series: pd.Series, default: int = 255, cap: int = 1000) -> int:
    # Estimate string length for VARCHAR(N)
    s = series.dropna().astype(str)
    if s.empty:
        return default
    max_len = int(s.map(len).max())
    # round up a bit, cap for sanity
    if max_len <= 0:
        return default
    return min(max(default, max_len), cap)


def pandas_dtype_to_sql(dtype: pd.api.types.CategoricalDtype | object, series: pd.Series) -> str:
    # Order matters; pandas nullable dtypes supported
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    if pd.api.types.is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    # fallback string
    n = _infer_varchar_len(series)
    return f"VARCHAR({n})"


def pandas_dtype_to_jsonschema(dtype: object, series: pd.Series) -> dict:
    if pd.api.types.is_bool_dtype(dtype):
        return {"type": ["boolean", "null"]}
    if pd.api.types.is_integer_dtype(dtype):
        return {"type": ["integer", "null"]}
    if pd.api.types.is_float_dtype(dtype):
        return {"type": ["number", "null"]}
    if pd.api.types.is_datetime64_any_dtype(dtype):
        # JSON Schema uses string + format for datetime
        return {"type": ["string", "null"], "format": "date-time"}
    # string
    max_len = None
    s = series.dropna().astype(str)
    if not s.empty:
        max_len = int(s.map(len).max())
    schema = {"type": ["string", "null"]}
    if max_len is not None:
        schema["maxLength"] = max_len
    return schema


def generate_create_table_sql(
    df: pd.DataFrame,
    table_name: str = "normalized_data",
    schema_name: Optional[str] = None,
) -> str:
    full_table = _sql_safe_identifier(table_name)
    if schema_name:
        full_table = f"{_sql_safe_identifier(schema_name)}.{full_table}"

    lines = [f"CREATE TABLE {full_table} ("]
    col_defs = []

    for col in df.columns:
        safe_col = _sql_safe_identifier(str(col))
        series = df[col]
        sql_type = pandas_dtype_to_sql(series.dtype, series)
        nullable = series.isna().any()
        null_sql = "NULL" if nullable else "NOT NULL"
        col_defs.append(f"  {safe_col} {sql_type} {null_sql}")

    lines.append(",\n".join(col_defs))
    lines.append(");")
    return "\n".join(lines)


def generate_json_schema(
    df: pd.DataFrame,
    title: str = "NormalizedData",
) -> dict:
    properties: dict = {}
    required: list[str] = []

    for col in df.columns:
        name = str(col)
        series = df[col]
        properties[name] = pandas_dtype_to_jsonschema(series.dtype, series)
        if not series.isna().any():
            required.append(name)

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema
