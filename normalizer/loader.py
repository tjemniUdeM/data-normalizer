from __future__ import annotations

from pathlib import Path
import pandas as pd


class UnsupportedFileTypeError(ValueError):
    pass


def load_table(path: str | Path, sheet: str | int | None = None) -> pd.DataFrame:
    
    ##Load a CSV or Excel file into a DataFrame.
    ##- CSV: uses pandas read_csv
    ##- Excel: uses pandas read_excel (openpyxl engine)
    
    p = Path(path)
    ##reading file 
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    suffix = p.suffix.lower()

    if suffix == ".csv":
        # Keep everything as string initially to avoid pandas guessing wrong types too early.
        return pd.read_csv(p, dtype="string", keep_default_na=True, na_values=["", " ", "NA", "N/A", "null", "None"])
    if suffix in (".xlsx", ".xls"):
        # Default: first sheet if sheet is None
        return pd.read_excel(
            p,
            sheet_name=sheet if sheet is not None else 0,
            dtype="string",
            engine="openpyxl",
        )

    raise UnsupportedFileTypeError(f"Unsupported file type: {suffix}. Only .csv, .xls, .xlsx are supported.")
