"""Human-readable summaries and workbook inspection."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .models import TreeGeometryResult
from .validation import ValidationReport


def summarise_results(results: list[TreeGeometryResult]) -> str:
    """Return a short markdown summary of a batch of results."""
    n = len(results)
    n_est = sum(1 for r in results if r.height_m is not None)
    n_warn = sum(1 for r in results if r.warnings)
    by_conf: dict[str, int] = {}
    for r in results:
        by_conf[r.confidence] = by_conf.get(r.confidence, 0) + 1
    lines = [
        "# Results summary",
        "",
        f"- Trees processed: **{n}**",
        f"- Height estimated: **{n_est}**",
        f"- Rows with warnings: **{n_warn}**",
        "- Confidence distribution: " + ", ".join(f"{k}={v}" for k, v in sorted(by_conf.items())),
    ]
    return "\n".join(lines)


def format_validation(report: ValidationReport) -> str:
    """Format a validation report as plain text."""
    if not report.issues:
        return "Validation: no issues found."
    lines = [f"Validation: {report.n_errors} error(s), {report.n_warnings} warning(s)."]
    for issue in report.issues:
        lines.append(f"  [{issue.level.upper()}] {issue.tree_id}: {issue.message}")
    return "\n".join(lines)


def inspect_workbook(path: Path) -> str:
    """Return a text report of an XLSX workbook's structure (sheets, shapes)."""
    path = Path(path)
    xls = pd.ExcelFile(path)
    lines = [f"Workbook: {path.name}", f"Sheets ({len(xls.sheet_names)}): {xls.sheet_names}", ""]
    for sheet in xls.sheet_names:
        df = xls.parse(sheet, header=None)
        lines.append(f"- '{sheet}': {df.shape[0]} rows x {df.shape[1]} cols")
    return "\n".join(lines)
