# Methodology

This tool produces **preliminary geometric estimates** of tree dimensions for
outdoor-lighting pre-modelling (e.g. DIALux) from minimal inventory data
(species + trunk perimeter). It is **not** a calibrated regional allometric
model, a forest inventory, or an arboricultural assessment.

## 1. DAP (diameter at breast height)

`DBH = P / π`, where `P` is the trunk perimeter in cm, assuming an approximately
circular cross-section measured at ~1.30 m above ground (FAO convention, R1).
Trunk diameter in metres is `DBH / 100`.

Non-positive or missing perimeter yields no estimate and a warning.

## 2. Height — asymptotic (monomolecular) model

`H = 1.30 + (H∞ − 1.30) · [1 − exp(−DBH / k)]`

- `H∞` — **adopted** asymptotic height (m), a reference adult size per species.
  It is **not** a normative maximum or an absolute botanical maximum.
- `k` — **adopted** operational shape parameter (cm) governing the approach to
  `H∞`. It was assigned by size class / architecture and **not** calibrated
  against a local sample.
- Results are rounded to the nearest **0.5 m**.

Non-linear asymptotic functions are a standard family for height–diameter
relationships (R2). No statistical confidence interval is produced.

## 3. Height sensitivity band

`H_min = round₀.₅( max(2, 0.80·H) )`, `H_max = round₀.₅( 1.20·H )`.

This ±20 % range (with a 2 m lower floor) is an **operational sensitivity
scenario**, prudently representing variation in site, age, form, pruning and
identification. **It is not a statistical confidence interval.**

## 4. Crown architectural groups (heuristic)

> The crown layer is an engineering **heuristic**. It is not present in the
> source workbook, not a published species coefficient, and not calibrated.

Non-palm crown diameter:

```
D_raw    = crown_dbh_factor × trunk_diameter_m
D_limit  = crown_height_limit_fraction × H
D_crown  = min(D_raw, D_limit)
```

Default operational factors (overridable in `crown_parameters.csv`):

| Group | crown_dbh_factor | crown_height_limit | crown_depth_fraction |
|---|---|---|---|
| broad | 25 | 1.00 | 0.80 |
| intermediate | 22 | 0.80 | 0.70 |
| compact | 18 | 0.90 | 0.75 |
| narrow | 14 | 0.50 | 0.60 |

## 5. Palms (heuristic, lower confidence)

`D_crown = clip(0.35·H, 3.5 m, 6.0 m)`. Palm crown is not well explained by
stipe diameter; **field measurement is recommended**. Palms are always
`confidence = low`.

## 6. Crown base and depth

`crown_depth = crown_depth_fraction × H`; `crown_base_height = H − crown_depth`.

## 7. Projected crown area

`A = π · D_crown² / 4` (circular projection). This ignores real crown asymmetry
and uses a single diameter (X = Y); it serves pre-modelling only.

## 8. Crown sensitivity band

`uncertainty = max(0.20·D_crown, 1.5 m)`;
`D_min = max(0, D_crown − uncertainty)`, `D_max = D_crown + uncertainty`.
A sensitivity scenario, not a confidence interval.

## 9. Rounding conventions

- DAP: full precision internally; displayed to 1 decimal.
- Height and bands: nearest 0.5 m (reproduces the workbook).
- Crown dimensions: 2 decimals.

## 10. Pseudocode

```text
for each tree:
    if perimeter <= 0 or missing: warn; skip
    dbh = perimeter / pi
    params = species_parameters[common_name]  # else warn; skip
    if scientific_name diverges from params: warn
    H = round_half( 1.30 + (Hinf - 1.30) * (1 - exp(-dbh / k)) )
    H_min, H_max = band(H)                     # max(2,0.8H), 1.2H
    if dbh > 120: warn (extrapolation); confidence = low
    group = crown_groups[params.crown_group]
    if palm: D = clip(0.35*H, 3.5, 6.0); confidence = low
    else:    D = min(factor*trunk_m, limit*H)
    base, depth = H*(1-depth_frac), H*depth_frac
    area = pi * D**2 / 4
    emit result + confidence + warnings
```
