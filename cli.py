from __future__ import annotations

from pathlib import Path
import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from normalizer.loader import load_table, UnsupportedFileTypeError

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
) -> None:

    ##Load a CSV/Excel file and print basic info.

    sheet_val: str | int | None = sheet
    if sheet is not None and sheet.isdigit():
        sheet_val = int(sheet)

    try:
        df = load_table(input_path, sheet=sheet_val)
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
        _print_preview(df, max_rows=preview_rows)


if __name__ == "__main__":
    app()
