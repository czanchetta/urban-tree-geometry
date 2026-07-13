# Changes relative to the workbook

The height methodology is reproduced without modification. The items below are
**additions** and **transparency improvements**, not changes to the height math.

## No change (faithful reproduction)
- DAP = P/π; asymptotic height model; 0.5 m rounding; ±band with 2 m floor.
- Per-species H∞ and k values.
- All 62 heights and bands reproduce identically.

## Additions (new, clearly labelled)
- **Crown / DIALux geometry layer** (heuristic): crown diameter, palm rule,
  crown base height, crown depth, projected area, X/Y/Z parameters. Not present
  in the workbook.
- **Confidence classification** and **structured warnings** per tree.
- **Trunk diameter in metres** (`DAP/100`) as an explicit output.
- **Externalised parameters** (CSV) with override support.
- **Validation** (units, missing/negative perimeter, unknown species,
  extrapolation) surfaced as warnings.

## Transparency improvements
- Explicit separation of measured / derived / adopted / heuristic provenance.
- The ±band is documented as an operational sensitivity range, not a CI.
- Taxonomic divergences and incomplete IDs are re-detected in code.

## Data
- Original client workbook **not** published; a **synthetic anonymised** demo
  dataset is provided instead.
