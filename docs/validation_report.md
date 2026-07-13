# Spreadsheet audit and validation report

**Source workbook:** `estimativa_altura_arvores_metodologia_fontes_dados.xlsx`
**Audit date:** 2026-07-13
**Auditor role:** scientific software engineer / dendrometric modelling review

This report documents the audit of the source workbook (Etapa 1) and the
regression validation of the Python reproduction against it. It is the
authoritative record of what the workbook contains, what was interpreted, what
was changed, and what was verified.

---

## 1. Sheets identified

| Sheet (original) | Function | Rows × cols |
|---|---|---|
| `Estimativa de altura` | Calculation memory (per-row formulas) | 63 × 12 |
| `Parâmetros` | Adopted parameters per species | 27 × 7 |
| `Metodologia e fontes` | Methodology, hypotheses and references | 50 × 3 |
| `Dados consolidados` | Formula-free consolidated output | 65 × 10 |

## 2. Counts

- **Trees (tree units):** 62 (UA01–UA62).
- **Species with adopted parameters:** 26 (all present in the inventory; no
  orphan species in either direction).
- **Distinct scientific names recorded:** 26 popular names, 2 of which carry a
  taxonomic divergence (see §7).

## 3. Field classification (measured / derived / adopted / heuristic)

| Kind | Fields |
|---|---|
| **Measured / project** | tree unit id, common name, scientific name, trunk perimeter (cm) |
| **Derived** | DAP (cm), total height (m), height ±band (m) |
| **Adopted** | H∞ (asymptotic height, m), k (shape parameter, cm) per species |
| **Heuristic** | *(none in the workbook)* — all crown/DIALux geometry is added by this project and labelled heuristic |
| **Reference** | source URLs and reference basis per species; R1–R9 bibliography |

## 4. Formulas found (reproduced exactly)

| Quantity | Workbook formula | Reproduced in |
|---|---|---|
| DAP | `=IFERROR(IF(E>0, E/PI(), ""), "")` | `calculations.dbh_from_perimeter` |
| Height | `=ROUND((1.30+(K-1.30)*(1-EXP(-F/L)))*2,0)/2` | `calculations.height_from_dbh` |
| Lower band | `=ROUND(MAX(2, G*0.8)*2,0)/2` | `calculations.height_band` |
| Upper band | `=ROUND(G*1.2*2,0)/2` | `calculations.height_band` |

Notes:
- Height rounds to the nearest **0.5 m**.
- The lower band applies a **2 m floor** and operates on the **already-rounded**
  height, then re-rounds to 0.5 m — reproduced faithfully.
- The ±20 % band is documented in the workbook as an **operational sensitivity
  range**, explicitly **not** a statistical confidence interval.

## 5. Parameters per species

H∞ ranges 6–30 m; k ranges 15–55 cm; both are declared in the workbook as
adopted references (adult reference size / operational shape), **not** locally
calibrated coefficients and **not** absolute maxima. Externalised verbatim to
`data/parameters/species_parameters.csv`.

## 6. Missing / blank values

- **5 rows (UA02–UA06)** have a blank per-row `k` cell in the calculation sheet,
  yet their cached height matches exactly when the **`Parâmetros`-sheet k** is
  used. The `Parâmetros` table is therefore the authoritative parameter source;
  the blank cells are a data-entry omission in the calc sheet, **not** a formula
  error. Confirmed by reproducing all 5 heights.
- No `#DIV/0!`, `#VALUE!`, `#REF!`, `#NAME?` cells were found.
- No zero or negative perimeters were found in the source data.

## 7. Taxonomic inconsistencies (workbook-flagged)

| Tree | Common name | Recorded scientific name | Note |
|---|---|---|---|
| UA06 | AMENDOIM DO CAMPO | *Anadenanthera colubrina* | diverges; height from common name |
| UA07 | ANGICO BRANCO | *Platypodium elegans* | diverges; height from common name |

Both are flagged in the workbook itself. The code re-detects the divergence and
attaches a warning.

## 8. Incomplete botanical identification (lower confidence)

Genus- or family-level identification only, flagged "baixa confiabilidade" in
`Parâmetros`:

- UA19 **PATA DE VACA** → *Bauhinia* (genus)
- UA30 **ALBIZIA** → *Fabaceae* (family)
- UA43 **CHICHA** → *Sterculia* (genus)

Marked `confidence = low` in the parameter set.

## 9. Extreme values / extrapolation

- **UA50**: perimeter 520 cm → DAP ≈ 165 cm. This is a large extrapolation of
  the adopted height curve. Retained (not dropped); the pipeline attaches an
  extrapolation warning and lowers confidence.

## 10. Palms

- **UA21, UA37** (*Syagrus romanzoffiana*, palm) use the same DAP–height model
  as broadleaf trees in the workbook. The workbook itself notes this is poorly
  suited to palms. The code keeps the workbook height for regression fidelity
  but treats palm **crown** geometry with a dedicated rule and `confidence = low`.

## 11. Units

All perimeters and heights are internally consistent (cm for perimeter/DAP, m
for height). Trunk diameter in metres is `DAP_cm / 100`. No cm/m confusion was
found. A `>700 cm` perimeter warning guards against mm-entered values on new
data.

## 12. Sensitive / proprietary content — NOT published

The `Metodologia e fontes` sheet cites project-identifying information — the
contracting authority, the project/site name, and the source project document
(PDF). The specific values are **not reproduced here**; they are recorded only in
the git-ignored private audit file (`data/private/AUDIT_SENSITIVE.md`). The
anonymisation policy and categories are documented in
[`audit/do_not_publish.md`](audit/do_not_publish.md).

The real inventory (tree IDs + perimeters) is client project data. **The
original workbook is excluded from the public repository.** The public demo uses
a synthetic, anonymised dataset (`data/raw/sample_tree_inventory.csv`) that
preserves statistical variety only.

---

## 13. Regression validation result

The Python height core was run against all **62** rows of the workbook's
formula-free `Dados consolidados` sheet.

| Metric | Result |
|---|---|
| Rows compared | 62 |
| **Identical** (DAP to 1 dp, H, both bands) | **62 / 62** |
| Within tolerance only | 0 |
| Divergent | 0 |

Tolerances: DBH ±0.05 cm (1-dp display); height and bands exact (0.5 m grid).
Reproducible via `python scripts/validate_workbook.py --reference tests/fixtures/workbook_reference.csv`
and the parametrized test `tests/test_regression_workbook.py`.

**Conclusion:** the height core is a faithful, bit-for-bit reproduction of the
workbook. The crown/DIALux layer is a separate engineering heuristic and is not
validated against the workbook because the workbook contains no crown data.
