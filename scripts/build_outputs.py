"""Run the pipeline on the demonstration inventory and write all outputs.

Produces:
    data/processed/dialux_tree_parameters.csv   (formula-free DIALux table)
    outputs/sample_results.csv                  (full result table)
    outputs/sample_results.xlsx                 (formula-free workbook)
    outputs/validation_summary.md               (batch summary)

Run:
    python scripts/build_outputs.py
"""

from __future__ import annotations

from pathlib import Path

from urban_tree_geometry import io as tio
from urban_tree_geometry.parameters import load_parameter_set
from urban_tree_geometry.pipeline import process_many
from urban_tree_geometry.reporting import format_validation, summarise_results
from urban_tree_geometry.validation import validate_trees

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "sample_tree_inventory.csv"


def main() -> None:
    trees = tio.read_inventory(RAW)
    params = load_parameter_set()
    results = process_many(trees, params)

    (ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "outputs").mkdir(parents=True, exist_ok=True)

    # formula-free DIALux hand-off table
    tio.dialux_dataframe(results).to_csv(
        ROOT / "data" / "processed" / "dialux_tree_parameters.csv", index=False
    )
    # full result table + workbook
    tio.write_results_csv(results, ROOT / "outputs" / "sample_results.csv")
    tio.write_results_excel(results, ROOT / "outputs" / "sample_results.xlsx")

    # validation + summary
    report = validate_trees(trees)
    summary = summarise_results(results)
    (ROOT / "outputs" / "validation_summary.md").write_text(
        summary + "\n\n## Validation\n\n```\n" + format_validation(report) + "\n```\n",
        encoding="utf-8",
    )
    print(summary)
    print(f"\nWrote outputs to {ROOT / 'outputs'} and data/processed/")


if __name__ == "__main__":
    main()
