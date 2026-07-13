# Data dictionary

Kinds: **measured** (project), **derived** (computed), **adopted** (literature
parameter), **heuristic** (engineering assumption, not from the workbook).

## Input — inventory (`data/raw/*.csv`)

| Field | Description | Unit | Type | Origin | Required | Example | Validation |
|---|---|---|---|---|---|---|---|
| tree_id | Unique tree/unit identifier | — | str | measured | TREE-001 | non-empty; unique |
| common_name | Popular species name | — | str | measured | ANGICO BRANCO | matched to parameters |
| scientific_name | Scientific name (may diverge) | — | str | measured | Anadenanthera colubrina | optional |
| perimeter_cm | Trunk perimeter at ~1.30 m | cm | float | measured | 120 | > 0; > 700 warns |

## Output — result / DIALux table

| Field | Description | Unit | Type | Origin |
|---|---|---|---|---|
| dbh_cm | DAP = P/π | cm | float | derived |
| trunk_diameter_m | DAP / 100 | m | float | derived |
| height_m / total_height_z_m | Estimated total height (Z) | m | float | derived |
| height_min_m / height_max_m | ±20 % sensitivity band (2 m floor) | m | float | derived |
| crown_diameter_x_m | Crown diameter, horizontal (X) | m | float | heuristic |
| crown_diameter_y_m | Crown diameter, orthogonal (Y = X) | m | float | heuristic |
| crown_base_height_m | Height to base of crown | m | float | heuristic |
| crown_depth_m | Vertical crown extent | m | float | heuristic |
| crown_projected_area_m2 | π·D²/4 (circular) | m² | float | heuristic |
| crown_min_m / crown_max_m | Crown sensitivity band | m | float | heuristic |
| crown_group | Architectural group | — | str | heuristic |
| confidence | low / medium / high | — | str | derived |
| warnings | Methodological alerts (`;`-joined) | — | str | derived |

## Parameters — `species_parameters.csv`

| Field | Description | Unit | Kind |
|---|---|---|---|
| common_name | Species key | — | measured |
| scientific_name | Reference scientific name | — | reference |
| height_asymptote_m | H∞ | m | adopted |
| height_shape_k_cm | k | cm | adopted |
| size_class | Porte class | — | reference |
| crown_group | Architectural group | — | heuristic |
| crown_method | dbh_scaled / palm_height_scaled | — | heuristic |
| confidence | Base confidence | — | heuristic |
| reference_basis, limitation, source_url | Provenance | — | reference |

## Parameters — `crown_parameters.csv` (all heuristic)
`crown_group, crown_dbh_factor, crown_height_limit_fraction,
crown_depth_fraction, crown_method, description`.

## Parameters — `palm_rule.csv` (all heuristic)
`palm_crown_height_factor (0.35), palm_crown_min_m (3.5), palm_crown_max_m (6.0)`.
