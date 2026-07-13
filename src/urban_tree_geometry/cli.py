"""Command-line interface for urban-tree-geometry.

Commands:
    calculate         estimate geometry from an inventory table
    validate          validate an inventory table without computing
    inspect-workbook  report the structure of an XLSX workbook
    export-excel      convert a results CSV into a formula-free XLSX
"""

from __future__ import annotations

from pathlib import Path

import typer

from . import __version__
from . import io as tio
from .parameters import load_parameter_set
from .pipeline import process_many
from .reporting import format_validation, inspect_workbook, summarise_results
from .validation import validate_columns, validate_trees

app = typer.Typer(
    add_completion=False,
    help="Preliminary tree geometry parameters for outdoor lighting models (DIALux).",
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"urban-tree-geometry {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True, help="Show version."
    ),
) -> None:
    """Root callback (enables ``--version``)."""


@app.command()
def calculate(
    input: Path = typer.Option(..., "--input", "-i", exists=True, help="Inventory CSV/XLSX."),
    output: Path = typer.Option(..., "--output", "-o", help="Output CSV path."),
    parameters: Path | None = typer.Option(
        None, "--parameters", "-p", help="Species parameter CSV/YAML/JSON (optional)."
    ),
    excel: Path | None = typer.Option(
        None, "--excel", help="Also write a formula-free XLSX to this path."
    ),
) -> None:
    """Estimate geometry parameters from an inventory table."""
    trees = tio.read_inventory(input)
    params = load_parameter_set(species_path=parameters)
    results = process_many(trees, params)
    tio.write_results_csv(results, output)
    typer.echo(summarise_results(results).replace("\n", "\n"))
    typer.echo(f"\nWrote {len(results)} rows to {output}")
    if excel is not None:
        tio.write_results_excel(results, excel)
        typer.echo(f"Wrote formula-free workbook to {excel}")


@app.command()
def validate(
    input: Path = typer.Option(..., "--input", "-i", exists=True, help="Inventory CSV/XLSX."),
) -> None:
    """Validate an inventory table. Exits non-zero if errors are found."""
    import pandas as pd

    df = pd.read_excel(input) if input.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(input)
    missing = validate_columns([str(c) for c in df.columns])
    if missing:
        typer.echo(f"ERROR: missing required column(s): {missing}", err=True)
        raise typer.Exit(code=2)

    trees = tio.read_inventory(input)
    report = validate_trees(trees)
    typer.echo(format_validation(report))
    if not report.ok:
        raise typer.Exit(code=1)


@app.command("inspect-workbook")
def inspect_workbook_cmd(
    input: Path = typer.Option(..., "--input", "-i", exists=True, help="XLSX workbook."),
) -> None:
    """Report the structure of an XLSX workbook (sheets and shapes)."""
    typer.echo(inspect_workbook(input))


@app.command("export-excel")
def export_excel(
    input: Path = typer.Option(..., "--input", "-i", exists=True, help="Results CSV."),
    output: Path = typer.Option(..., "--output", "-o", help="Output XLSX path."),
) -> None:
    """Convert a results CSV into a formula-free XLSX (with a DIALux sheet)."""
    import pandas as pd

    from .models import TreeGeometryResult

    df = pd.read_csv(input)
    results = []
    for rec in df.to_dict(orient="records"):
        warnings = rec.pop("warnings", "") or ""
        rec = {k: (None if pd.isna(v) else v) for k, v in rec.items()}
        rec["warnings"] = [w.strip() for w in str(warnings).split(";") if w.strip()]
        results.append(TreeGeometryResult(**rec))
    tio.write_results_excel(results, output)
    typer.echo(f"Wrote formula-free workbook to {output}")


def _load_results(input: Path):
    """Read an inventory or results table and return computed results."""
    from .pipeline import process_many

    trees = tio.read_inventory(input)
    params = load_parameter_set()
    return process_many(trees, params)


@app.command("export-3ds")
def export_3ds_cmd(
    input: Path = typer.Option(..., "--input", "-i", exists=True, help="Inventory CSV/XLSX."),
    outdir: Path = typer.Option(..., "--outdir", "-o", help="Directory for the .3ds files."),
) -> None:
    """Export one schematic ``.3ds`` per tree (native DIALux import format).

    Builds a trunk+crown primitive mesh sized to each tree's computed geometry.
    The mesh is a heuristic stand-in volume, not a survey-accurate tree.
    """
    from . import dialux_export as dx

    outdir.mkdir(parents=True, exist_ok=True)
    results = _load_results(input)
    written, skipped = 0, []
    for r in results:
        try:
            path = outdir / f"{r.tree_id}.3ds"
            dx.write_3ds(r, path)
            written += 1
        except dx.ExportError as e:
            skipped.append(f"{r.tree_id}: {e}")
    typer.echo(f"Wrote {written} .3ds file(s) to {outdir}")
    for s in skipped:
        typer.echo(f"  skipped {s}", err=True)


@app.command("export-dxobj")
def export_dxobj_cmd(
    input: Path = typer.Option(..., "--input", "-i", exists=True, help="Inventory CSV/XLSX."),
    template: Path = typer.Option(
        ..., "--template", "-t", exists=True, help="User-supplied DIALux .dxobj template."
    ),
    outdir: Path = typer.Option(..., "--outdir", "-o", help="Directory for the .dxobj files."),
) -> None:
    """Export one ``.dxobj`` per tree by resizing a DIALux template.

    Only the STEP dimensions / scale factors are rewritten; the template's
    proprietary mesh is reused. The template is your own DIALux asset and is
    never committed to this repository.
    """
    from . import dialux_export as dx

    outdir.mkdir(parents=True, exist_ok=True)
    results = _load_results(input)
    written, skipped = 0, []
    for r in results:
        try:
            dx.rewrite_dxobj(r, template, outdir / f"{r.tree_id}.dxobj")
            written += 1
        except dx.ExportError as e:
            skipped.append(f"{r.tree_id}: {e}")
    typer.echo(f"Wrote {written} .dxobj file(s) to {outdir}")
    for s in skipped:
        typer.echo(f"  skipped {s}", err=True)


if __name__ == "__main__":
    app()
