# DIALux parameters

| Estimated parameter | Role in the 3D object |
|---|---|
| `total_height_z_m` | **Z** — total height |
| `crown_diameter_x_m` | **X** — horizontal crown diameter |
| `crown_diameter_y_m` | **Y** — orthogonal diameter (= X here) |
| `trunk_diameter_m` | trunk diameter |
| `crown_base_height_m` | height to crown base |
| `crown_depth_m` | vertical crown extent |

The DIALux table (`data/processed/dialux_tree_parameters.csv` and the `dialux`
sheet of the XLSX) contains **fixed values only**, no formulas.

!!! note "No automatic import format"
    This project makes **no** claim of an automatic DIALux import format. Confirm
    modelling capabilities in the official DIALux documentation. Where a field
    survey exists, replace X and Y with the two real orthogonal diameters
    measured on site.
