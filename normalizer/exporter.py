from __future__ import annotations

from pathlib import Path
import json
import pandas as pd


def ensure_outdir(outdir: str | Path) -> Path:
    p = Path(outdir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def export_clean_csv(df: pd.DataFrame, outdir: Path, filename: str = "clean.csv") -> Path:
    path = outdir / filename
    df.to_csv(path, index=False)
    return path


def export_json_records(df: pd.DataFrame, outdir: Path, filename: str = "data.json") -> Path:
    path = outdir / filename
    # Convert datetimes to ISO strings; keep nulls as null
    records = df.where(df.notna(), None).to_dict(orient="records")
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=str)
    return path


def export_text(text: str, outdir: Path, filename: str) -> Path:
    path = outdir / filename
    path.write_text(text, encoding="utf-8")
    return path


def export_json(obj: dict, outdir: Path, filename: str) -> Path:
    path = outdir / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path
