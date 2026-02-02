from __future__ import annotations

from pathlib import Path
import pandas as pd
import json
import typer
from datetime import date
from pathlib import Path
from rich.console import Console
from rich.table import Table

from normalizer.loader import load_table, UnsupportedFileTypeError
from normalizer.profiler import profile_dataframe
from normalizer.cleaner import normalize_dataframe
from normalizer.schema import generate_create_table_sql, generate_json_schema
from normalizer.exporter import (
    ensure_outdir,
    export_clean_csv,
    export_json_records,
    export_text,
    export_json,
)


app = typer.Typer(add_completion=False)
console = Console() ## rich console 

## Helper function 
def _print_preview(df: pd.DataFrame, max_rows: int = 5) -> None:
    table = Table(title="Preview", show_lines=False) ##rich table
    for col in df.columns[:10]:  # avoid huge tables in terminal
        table.add_column(str(col), overflow="fold")

    preview = df.head(max_rows)

    for _, row in preview.iterrows():
        table.add_row(*[str(row.get(c, "")) if row.get(c, "") is not pd.NA else "" for c in preview.columns[:10]])

    console.print(table)


@app.command()
def run(
    input_path: str = typer.Argument(..., help="Path to input .csv or .xlsx/.xls file"),
    sheet: str = typer.Option(None, "--sheet", help="Excel sheet name or index (e.g. 'Sheet1' or '0')"),
    preview_rows: int = typer.Option(5, "--preview-rows", min=0, max=50, help="How many rows to preview"),
    table_name: str = typer.Option("normalized_data", "--table", help="SQL table name"),
    show_schema: bool = typer.Option(False, "--show-schema/--no-show-schema", help="Print generated schemas"),
    outdir: str = typer.Option("", "--out", help="Subfolder inside ./output (e.g. 'results')"),
    export_files: bool = typer.Option(False, "--export", help="Write outputs to files"),
    overwrite: bool = typer.Option(True,"--overwrite/--no-overwrite",help="Overwrite existing output files",),



) -> None:
    ## prepare output path
    
    input_path_obj = Path(input_path)
    output_prefix = f"{input_path_obj.stem}OUT"
    
    run_date = date.today().isoformat()  # e.g. 2026-02-02
    run_folder_name = f"{output_prefix}_{run_date}"


    ##Load a CSV/Excel file and print basic info.
    sheet_val: str | int | None = sheet
    if sheet is not None and sheet.isdigit():
        sheet_val = int(sheet)

    try:
        df = load_table(input_path, sheet=sheet_val)
        #if the file is empty 
        if df.empty:
            console.print("[red]Error:[/red] Input file contains no rows.")
            raise typer.Exit(code=5)

        profiles = profile_dataframe(df)
        #_print_profile(profiles)
        df_clean = normalize_dataframe(df, profiles)
        #in case there is an unsusable column 
        if df_clean.shape[1] == 0:
            console.print("[red]Error:[/red] No usable columns after normalization.")
            raise typer.Exit(code=6)
        create_sql = generate_create_table_sql(df_clean, table_name=table_name)
        json_schema = generate_json_schema(df_clean, title=table_name)
        if export_files:
            base_root = ensure_outdir("output")  # always the root
            base_out_path = ensure_outdir(base_root / outdir) if outdir else base_root

            out_path = base_out_path / run_folder_name
            if out_path.exists() and not overwrite:
                console.print(f"[red]Error:[/red] Output folder already exists: {out_path}")
                console.print("Run again with --overwrite or choose a different --out directory.")
                raise typer.Exit(code=4)
            out_path = ensure_outdir(base_out_path / run_folder_name)

            clean_csv_path = export_clean_csv(
            df_clean, out_path, f"{output_prefix}_clean.csv"
            )
            json_data_path = export_json_records(
                df_clean, out_path, f"{output_prefix}_data.json"
            )
            sql_path = export_text(
                create_sql, out_path, f"{output_prefix}_schema.sql"
            )
            json_schema_path = export_json(
                json_schema, out_path, f"{output_prefix}_schema.json"
            )
            # simple report: profiles + row/col counts
            report = {
                "rows": int(len(df_clean)),
                "columns": int(len(df_clean.columns)),
                "profiles": [
                    {
                        "name": p.name,
                        "inferred_type": p.inferred_type,
                        "missing_pct": p.missing_pct,
                        "unique_count": p.unique_count,
                        "samples": p.samples,
                    }
                    for p in profiles
                ],
            }
            
            report_path = export_json(
                report, out_path, f"{output_prefix}_report.json"
            )

            console.print("\n[bold]Exported files:[/bold]")
            console.print(f"  • {clean_csv_path}")
            console.print(f"  • {json_data_path}")
            console.print(f"  • {sql_path}")
            console.print(f"  • {json_schema_path}")
            console.print(f"  • {report_path}")

        if show_schema:
            console.print("\n[bold]SQL Schema (CREATE TABLE)[/bold]")
            console.print(create_sql)

            console.print("\n[bold]JSON Schema[/bold]")
            console.print_json(json.dumps(json_schema))



    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except UnsupportedFileTypeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=2)
    except Exception as e:
        console.print(f"[red]Unexpected error while reading file:[/red] {e}")
        raise typer.Exit(code=3)

    console.print(f"[bold]Loaded:[/bold] {Path(input_path).name}")
    console.print(f"[bold]Rows:[/bold] {len(df):,}")
    console.print(f"[bold]Columns:[/bold] {len(df.columns):,}")

    # Column list (limit)
    cols = [str(c) for c in df.columns]
    console.print("[bold]Column names (up to 30):[/bold]")
    for c in cols[:30]:
        console.print(f"  • {c}")
    if len(cols) > 30:
        console.print(f"  ... +{len(cols) - 30} more")

    if preview_rows > 0:
        console.print("\n[bold]Cleaned Preview[/bold]")
        _print_preview(df_clean, max_rows=preview_rows)


def _print_profile(profiles):
    table = Table(title="Column Profile", show_lines=False)

    table.add_column("Column")
    table.add_column("Type")
    table.add_column("Missing %", justify="right")
    table.add_column("Unique", justify="right")
    table.add_column("Samples")

    for p in profiles:
        table.add_row(
            p.name,
            p.inferred_type,
            f"{p.missing_pct}%",
            str(p.unique_count),
            ", ".join(p.samples),
        )

    console.print(table)

def main():
    app()

if __name__ == "__main__":
    app()


