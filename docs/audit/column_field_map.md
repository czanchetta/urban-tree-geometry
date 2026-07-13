# Map: workbook columns → code fields

## `Estimativa de altura` (calculation memory)

| Column | Header | Code field | Kind |
|---|---|---|---|
| A | Item | (row index) | — |
| B | Unidade arbórea | `tree_id` | measured |
| C | Espécie | `common_name` | measured |
| D | Nome científico | `scientific_name` | measured |
| E | Perímetro (cm) | `perimeter_cm` | measured |
| F | DAP estimado (cm) | `dbh_cm` | derived |
| G | Altura estimada (m) | `height_m` | derived |
| H | Faixa inferior (m) | `height_min_m` | derived |
| I | Faixa superior (m) | `height_max_m` | derived |
| J | Observação | `warnings` | reference |
| K | H∞ adotado (m) | `SpeciesParameters.height_asymptote_m` | adopted |
| L | k adotado (cm) | `SpeciesParameters.height_shape_k_cm` | adopted |

## `Parâmetros`

| Column | Header | Code field |
|---|---|---|
| A | Espécie | `common_name` |
| B | H∞ adotado (m) | `height_asymptote_m` |
| C | k adotado (cm) | `height_shape_k_cm` |
| D | Classe de porte | `size_class` |
| E | Base da dimensão de referência | `reference_basis` |
| F | Interpretação / limitação | `limitation` |
| G | Fonte principal | `source_url` |

## `Dados consolidados` → regression fixture
Columns A–J map to `tests/fixtures/workbook_reference.csv`
(tree_id, common_name, scientific_name, perimeter_cm, dap_cm, height_m,
height_min_m, height_max_m, obs).

## Code fields with no workbook column (heuristic additions)
`trunk_diameter_m`, `crown_diameter_x_m`, `crown_diameter_y_m`,
`crown_base_height_m`, `crown_depth_m`, `crown_projected_area_m2`,
`crown_min_m`, `crown_max_m`, `crown_group`, `confidence`.
