"""Input/output: read inventory tables and write results (CSV / XLSX).

The XLSX writer emits a formula-free workbook (fixed values only), suitable as
the DIALux hand-off table.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .models import TreeGeometryResult, TreeInput

# Column aliases accepted on input (case-insensitive) -> canonical field.
_INPUT_ALIASES = {
    "tree_id": "tree_id",
    "id": "tree_id",
    "unidade_arborea": "tree_id",
    "ua": "tree_id",
    "common_name": "common_name",
    "especie": "common_name",
    "nome_popular": "common_name",
    "scientific_name": "scientific_name",
    "nome_cientifico": "scientific_name",
    "perimeter_cm": "perimeter_cm",
    "perimetro_cm": "perimeter_cm",
    "perimetro": "perimeter_cm",
}

# Ordered columns for the formula-free DIALux export.
DIALUX_COLUMNS = [
    "tree_id",
    "common_name",
    "scientific_name",
    "total_height_z_m",
    "crown_diameter_x_m",
    "crown_diameter_y_m",
    "trunk_diameter_m",
    "crown_base_height_m",
    "crown_depth_m",
    "crown_projected_area_m2",
    "crown_min_m",
    "crown_max_m",
    "height_min_m",
    "height_max_m",
    "confidence",
    "warnings",
]


def read_inventory(path: Path) -> list[TreeInput]:
    """Read an inventory CSV/XLSX into a list of :class:`TreeInput`."""
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    rename = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_")
        if key in _INPUT_ALIASES:
            rename[col] = _INPUT_ALIASES[key]
    df = df.rename(columns=rename)

    trees: list[TreeInput] = []
    for _, row in df.iterrows():
        trees.append(
            TreeInput(
                tree_id=str(row.get("tree_id", "")).strip(),
                common_name=_opt_str(row.get("common_name")),
                scientific_name=_opt_str(row.get("scientific_name")),
                perimeter_cm=_opt_float(row.get("perimeter_cm")),
            )
        )
    return trees


def results_to_dataframe(results: list[TreeGeometryResult]) -> pd.DataFrame:
    """Flatten results into a DataFrame (warnings joined with '; ')."""
    rows = []
    for r in results:
        d = r.model_dump()
        d["warnings"] = "; ".join(r.warnings)
        rows.append(d)
    return pd.DataFrame(rows)


def write_results_csv(results: list[TreeGeometryResult], path: Path) -> None:
    """Write the full result table to CSV."""
    results_to_dataframe(results).to_csv(Path(path), index=False)


def dialux_dataframe(results: list[TreeGeometryResult]) -> pd.DataFrame:
    """Build the formula-free DIALux hand-off table (fixed values only)."""
    df = results_to_dataframe(results).copy()
    df["total_height_z_m"] = df["height_m"]
    for col in DIALUX_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[DIALUX_COLUMNS]


def write_results_excel(
    results: list[TreeGeometryResult], path: Path, dialux_sheet: bool = True
) -> None:
    """Write results to a formula-free XLSX (full table + optional DIALux sheet)."""
    full = results_to_dataframe(results)
    with pd.ExcelWriter(Path(path), engine="openpyxl") as writer:
        full.to_excel(writer, sheet_name="results", index=False)
        if dialux_sheet:
            dialux_dataframe(results).to_excel(writer, sheet_name="dialux", index=False)


def _opt_str(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return s or None


def _opt_float(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
