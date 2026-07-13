# Funcionamento

## Entrada
Uma tabela de inventário com, no mínimo: `tree_id`, `common_name`,
`scientific_name`, `perimeter_cm`.

## Etapas
1. **DAP** — `DAP = P/π` (cm); diâmetro do tronco `= DAP/100` (m).
2. **Altura** — modelo assintótico `H = 1,30 + (H∞ − 1,30)·[1 − exp(−DAP/k)]`,
   arredondada a 0,5 m.
3. **Faixa de altura** — `máx(2; 0,8·H)` a `1,2·H` (cenário de sensibilidade).
4. **Dossel (heurístico)** — `D = mín(fator·tronco; limite·H)`; palmeiras
   `D = clip(0,35·H; 3,5; 6,0)`.
5. **Base, profundidade e área** da copa.
6. **Confiabilidade e advertências** por árvore.

## Saída
Tabela de resultados e **tabela DIALux sem fórmulas** (X, Y, Z e demais campos).

<figure markdown>
  ![Parâmetros geométricos](assets/geometry.svg)
  <figcaption>Correspondência entre os parâmetros estimados e a geometria 3D.</figcaption>
</figure>
