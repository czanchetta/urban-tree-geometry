# Methodology

!!! warning "Methodological disclaimer"
    Results are **preliminary estimates** for lighting pre-modelling. The tool
    **does not replace** field dendrometric survey, forest inventory,
    arboricultural report, stability assessment or topographic survey. Parameters
    are not locally calibrated; the ranges are **sensitivity scenarios**, not
    statistical confidence intervals. Real crowns may be asymmetric; pruning and
    urban conditions change the geometry; palms carry higher uncertainty; trees
    near luminaires should be measured in the field.

## DBH
`DBH = P/π`, assuming a circular section measured at ~1.30 m (FAO convention).

## Height
`H = 1.30 + (H∞ − 1.30)·[1 − exp(−DBH/k)]`. `H∞` is an **adopted** adult
reference size per species (not a normative maximum); `k` is an operational
parameter **not** locally calibrated. Result rounded to 0.5 m.

## Crown (heuristic)
Architectural groups with operational factors (broad 25, intermediate 22,
compact 18, narrow 14) and a per-group height limit. Palms use a dedicated rule.
These values are **not** published per-species dendrometric coefficients.

<figure markdown>
  ![Crown versus DBH](assets/crown_vs_dap.png)
  <figcaption>Heuristic crown diameter by architectural group.</figcaption>
</figure>

## Sensitivity
<figure markdown>
  ![Sensitivity analysis](assets/sensitivity_analysis.png)
  <figcaption>Effect of H∞, k, crown factor and height limit.</figcaption>
</figure>

The full methodology is in `docs/methodology.md` in the repository.
