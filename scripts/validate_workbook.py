"""Regression check: reproduce a reference workbook output with the package.

Given a formula-free reference CSV (columns: tree_id, common_name,
scientific_name, perimeter_cm, dap_cm, height_m, height_min_m, height_max_m),
recompute with the package and report identical / within-tolerance / divergent
rows with a probable cause for each divergence.

Run:
    python scripts/validate_workbook.py --reference tests/fixtures/workbook_reference.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from urban_tree_geometry.models import TreeInput
from urban_tree_geometry.parameters import load_parameter_set
from urban_tree_geometry.pipeline import process_tree

DBH_TOL = 0.05
H_TOL = 1e-9


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reference", type=Path, required=True)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    params = load_parameter_set()
    with args.reference.open(encoding="utf-8") as f:
        ref = list(csv.DictReader(f))

    identical, within_tol, divergent = [], [], []
    for row in ref:
        tree = TreeInput(
            tree_id=row["tree_id"],
            common_name=row["common_name"],
            scientific_name=row["scientific_name"],
            perimeter_cm=float(row["perimeter_cm"]),
        )
        res = process_tree(tree, params)
        dh = abs((res.height_m or -999) - float(row["height_m"]))
        dd = abs((res.dbh_cm or -999) - float(row["dap_cm"]))
        if dh == 0 and dd == 0:
            identical.append(row["tree_id"])
        elif dh <= H_TOL and dd <= DBH_TOL:
            within_tol.append(row["tree_id"])
        else:
            cause = "height differs" if dh > H_TOL else "dbh rounding"
            divergent.append((row["tree_id"], cause, res.height_m, row["height_m"]))

    lines = [
        "# Workbook regression report",
        "",
        f"- Rows compared: **{len(ref)}**",
        f"- Identical: **{len(identical)}**",
        f"- Within tolerance (DBH <= {DBH_TOL}, H exact): **{len(within_tol)}**",
        f"- Divergent: **{len(divergent)}**",
    ]
    if divergent:
        lines += ["", "## Divergences", ""]
        for tid, cause, got, exp in divergent:
            lines.append(f"- {tid}: {cause} (got {got}, expected {exp})")
    report_text = "\n".join(lines)
    print(report_text)
    if args.report:
        args.report.write_text(report_text + "\n", encoding="utf-8")
    return 0 if not divergent else 1


if __name__ == "__main__":
    raise SystemExit(main())
