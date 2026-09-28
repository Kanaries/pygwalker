import sys
from pathlib import Path
import typer
import polars as pl

from .server import walk_server

app = typer.Typer(name="pygwalker-cli", help="PyGWalker Standalone Fast CLI - Zero Jupyter required.")


@app.command()
def main(
    file_path: Path = typer.Argument(..., help="Path to CSV or Parquet dataset"),
    port: int = typer.Option(8080, "--port", "-p", help="Port for the FastAPI server"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Do not automatically open the web browser"),
):
    """Start standalone Graphic-Walker web server for a dataset."""
    if not file_path.exists():
        typer.echo(f"Error: File '{file_path}' not found.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Loading '{file_path}' into Polars Rust engine...")
    if file_path.suffix.lower() == ".csv":
        df = pl.read_csv(file_path, try_parse_dates=True, infer_schema_length=10000)
    elif file_path.suffix.lower() == ".parquet":
        df = pl.read_parquet(file_path)
    else:
        typer.echo("Unsupported file format. Please provide a CSV or Parquet file.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Loaded dataset with shape {df.shape}. Starting server...")
    walk_server(df, port=port, auto_open=not no_browser)


def entry_point():
    app()


if __name__ == "__main__":
    entry_point()
