# Conceptual DIALux workflow

This page explains, at a conceptual level, how the estimated parameters map to a
3D tree object in outdoor-lighting software such as DIALux. **It does not claim
any automatic import format**, and DIALux functionality should be confirmed
against the official DIALux documentation.

## Parameter → geometry mapping

| Estimated parameter | Role in a 3D tree object |
|---|---|
| `total_height_z_m` | **Z** — total height of the object |
| `crown_diameter_x_m` | **X** — horizontal crown diameter |
| `crown_diameter_y_m` | **Y** — orthogonal horizontal crown diameter (= X here) |
| `trunk_diameter_m` | trunk cylinder diameter, when modelled separately |
| `crown_base_height_m` | height from ground to the base of the crown |
| `crown_depth_m` | vertical extent of the crown body |

![Tree geometry parameters](assets/geometry.svg)

## Suggested steps (conceptual)

1. Place a tree/vegetation object at the luminaire-relevant location.
2. Set total height to **Z** (`total_height_z_m`).
3. Set the crown horizontal size using **X** and **Y**
   (`crown_diameter_x_m`, `crown_diameter_y_m`).
4. If the object supports a separate trunk and crown, set the trunk diameter
   (`trunk_diameter_m`), the crown base height (`crown_base_height_m`) and the
   crown depth (`crown_depth_m`).
5. Treat the sensitivity bands (`height_min/max_m`, `crown_min/max_m`) as
   alternative scenarios for a light-obstruction sensitivity check.

## Important

- When a field survey is available, replace **X** and **Y** with the two real
  orthogonal crown diameters measured on site — real crowns are rarely circular.
- For trees that directly obstruct or are illuminated by a fixture, measure the
  tree in the field; a preliminary estimate is not sufficient for photometric
  decisions.
- The `dialux` sheet in `outputs/sample_results.xlsx` and
  `data/processed/dialux_tree_parameters.csv` contain fixed values only (no
  formulas), suitable as a hand-off table.
