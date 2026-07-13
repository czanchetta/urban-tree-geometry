# Parâmetros DIALux

| Parâmetro estimado | Papel no objeto 3D |
|---|---|
| `total_height_z_m` | **Z** — altura total |
| `crown_diameter_x_m` | **X** — diâmetro horizontal do dossel |
| `crown_diameter_y_m` | **Y** — diâmetro ortogonal (= X aqui) |
| `trunk_diameter_m` | diâmetro do tronco |
| `crown_base_height_m` | altura da base da copa |
| `crown_depth_m` | profundidade vertical da copa |

A tabela DIALux (`data/processed/dialux_tree_parameters.csv` e a aba `dialux`
do XLSX) contém **apenas valores fixos**, sem fórmulas.

!!! note "Sem formato de importação automática"
    Este projeto **não** afirma existir um formato de importação automática no
    DIALux. Confirme os recursos de modelagem na documentação oficial do DIALux.
    Onde houver levantamento de campo, substitua X e Y pelos dois diâmetros
    ortogonais reais medidos.
