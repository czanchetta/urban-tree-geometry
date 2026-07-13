# Inconsistencies found in the source workbook

| # | Location | Inconsistency | Handling |
|---|---|---|---|
| 1 | UA06 | Common name AMENDOIM DO CAMPO vs scientific *Anadenanthera colubrina* | Workbook-flagged; height from common name; code re-warns |
| 2 | UA07 | Common name ANGICO BRANCO vs scientific *Platypodium elegans* | Workbook-flagged; height from common name; code re-warns |
| 3 | UA19 | PATA DE VACA identified only to genus *Bauhinia* | confidence = low |
| 4 | UA30 | ALBIZIA identified only to family *Fabaceae* | confidence = low |
| 5 | UA43 | CHICHA identified only to genus *Sterculia* | confidence = low |
| 6 | UA50 | Perimeter 520 cm → DAP ≈ 165 cm, large extrapolation | retained; extrapolation warning |
| 7 | UA21, UA37 | Palms use the broadleaf DAP–height model | height kept for fidelity; crown uses palm rule; confidence = low |
| 8 | UA02–UA06 | Blank per-row `k` in calc sheet | resolved via `Parâmetros` k (reproduces cached heights) |

No spreadsheet error cells (`#DIV/0!`, `#REF!`, etc.), zero, or negative
perimeters were present in the source data.
