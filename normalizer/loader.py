from __future__ import annotations

from pathlib import Path
import pandas as pd


class UnsupportedFileTypeError(ValueError):
    pass

def _detect_delimiter(path: str | Path) -> str:
    # Try common delimiters and pick the one that produces the most columns on sample lines.
    candidates = [",", ";", "\t", "|"]
    best_delim = ","
    best_score = 0

    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        sample_lines = [f.readline() for _ in range(30)]
    sample = "".join(sample_lines)

    for d in candidates:
        # crude but effective: average columns across non-empty lines
        lines = [ln for ln in sample_lines if ln.strip()]
        if not lines:
            continue
        counts = [ln.count(d) for ln in lines]
        score = sum(counts) / len(counts)
        if score > best_score:
            best_score = score
            best_delim = d

    return best_delim


def _read_csv_robust(path: str | Path) -> pd.DataFrame:
    delim = _detect_delimiter(path)
    return pd.read_csv(
        path,
        sep=delim,
        encoding="utf-8-sig",
        engine="c",
        dtype=str,            # keeps raw values; your normalizer can infer later
        keep_default_na=False # prevents "NA" becoming NaN unexpectedly
    )
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
        df = _read_csv_robust(path)
        return df
    if suffix in (".xlsx", ".xls"):
        # Default: first sheet if sheet is None
        return pd.read_excel(
            p,
            sheet_name=sheet if sheet is not None else 0,
            dtype="string",
            engine="openpyxl",
        )

    raise UnsupportedFileTypeError(f"Unsupported file type: {suffix}. Only .csv, .xls, .xlsx are supported.")
