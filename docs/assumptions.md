# Assumptions

Assumptions are grouped by kind. Adopted and heuristic values are **not**
measurements.

## Geometric assumptions
- Trunk cross-section is approximately circular (`DBH = P/π`).
- Crown projection is circular; the two horizontal diameters are equal (X = Y).
- Crown vertical extent is a single fraction of total height.

## Dendrometric assumptions
- Perimeter was measured at ~1.30 m above ground (breast height, FAO, R1).
- The height–diameter relationship follows a monomolecular asymptotic form (R2).
- `H∞` represents a plausible adult reference size per species, not a maximum.

## Data assumptions
- Species is identified by common name; the parameter set is keyed on it.
- Where scientific and common names diverge, the common name governs the estimate.
- Genus/family-only identifications carry lower confidence.

## Rounding assumptions
- Heights are meaningful only to 0.5 m at this preliminary stage.
- The lower height band is floored at 2 m.

## Engineering parameters (adopted / heuristic)
- `H∞`, `k`: adopted per species from literature; not locally calibrated.
- Crown factors, height-limit fractions, depth fractions: heuristic operational
  parameters by crown architecture.
- Palm rule constants (0.35, 3.5 m, 6.0 m): heuristic.
- Sensitivity bands (±20 % height; max(20 %, 1.5 m) crown): operational scenarios.
