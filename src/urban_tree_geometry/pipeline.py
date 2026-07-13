"""Orchestration: turn a :class:`TreeInput` into a :class:`TreeGeometryResult`.

The pipeline calls the *faithful height core* first, then the *heuristic crown
layer*, accumulating human-readable warnings and downgrading confidence when
inputs are missing, species are unknown, or values are extrapolations.
"""

from __future__ import annotations

from . import calculations as calc
from . import crown as crownmod
from .models import Confidence, TreeGeometryResult, TreeInput
from .parameters import ParameterSet

# DBH (cm) above which the height model is a notable extrapolation for the
# adopted curves in this dataset (flag, do not drop).
DBH_EXTRAPOLATION_CM = 120.0

_CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}


def _min_confidence(a: Confidence, b: Confidence) -> Confidence:
    return a if _CONFIDENCE_ORDER[a] <= _CONFIDENCE_ORDER[b] else b


def process_tree(
    tree: TreeInput,
    params: ParameterSet,
    height_asymptote_m: float | None = None,
    shape_k_cm: float | None = None,
) -> TreeGeometryResult:
    """Compute the full geometry result for one tree.

    Args:
        tree: the inventory record.
        params: the loaded parameter set.
        height_asymptote_m: optional per-tree override of H_inf.
        shape_k_cm: optional per-tree override of k.
    """
    warnings: list[str] = []
    result = TreeGeometryResult(
        tree_id=tree.tree_id,
        common_name=tree.common_name,
        scientific_name=tree.scientific_name,
        perimeter_cm=tree.perimeter_cm,
    )

    species = params.get_species(tree.common_name)
    if species is None:
        warnings.append(
            f"Species '{tree.common_name}' not found in parameter set; "
            "height and crown cannot be estimated. Provide parameters or overrides."
        )
        result.confidence = "low"
        result.warnings = warnings
        return result

    # Taxonomic consistency check (project name vs parameter set).
    if (
        tree.scientific_name
        and species.scientific_name
        and _norm(tree.scientific_name) != _norm(species.scientific_name)
    ):
        warnings.append(
            f"Recorded scientific name '{tree.scientific_name}' diverges from the "
            f"reference '{species.scientific_name}' for '{tree.common_name}'; "
            "estimate is based on the common name."
        )

    confidence: Confidence = species.confidence
    result.crown_group = species.crown_group

    # --- height core (faithful) ---
    h_inf = height_asymptote_m if height_asymptote_m is not None else species.height_asymptote_m
    k = shape_k_cm if shape_k_cm is not None else species.height_shape_k_cm

    try:
        dbh = calc.dbh_from_perimeter(tree.perimeter_cm)
    except calc.UnitError as exc:
        warnings.append(f"DBH not computed: {exc}.")
        result.confidence = "low"
        result.warnings = warnings
        return result

    result.dbh_cm = round(dbh, 1)
    result.trunk_diameter_m = round(calc.dbh_cm_to_trunk_diameter_m(dbh), 4)

    try:
        height = calc.height_from_dbh(dbh, h_inf, k)
    except (ValueError, calc.UnitError) as exc:
        warnings.append(f"Height not computed: {exc}.")
        result.confidence = "low"
        result.warnings = warnings
        return result

    result.height_m = height
    result.height_min_m, result.height_max_m = calc.height_band(height)

    if dbh > DBH_EXTRAPOLATION_CM:
        warnings.append(
            f"DBH {dbh:.0f} cm is a large extrapolation for the adopted height "
            "curve; treat the height with caution."
        )
        confidence = _min_confidence(confidence, "low")

    # --- heuristic crown / DIALux layer ---
    group = params.get_crown_group(species.crown_group)
    if group is None:
        warnings.append(f"Crown group '{species.crown_group}' not found; crown geometry skipped.")
        result.confidence = _min_confidence(confidence, "low")
        result.warnings = warnings
        return result

    if species.crown_method == "palm_height_scaled" or group.crown_method == "palm_height_scaled":
        crown_d = crownmod.crown_diameter_palm(height, params.palm_rule)
        warnings.append(
            "Palm crown estimated from height, not DBH; confidence is low. "
            "Field measurement is recommended."
        )
        confidence = _min_confidence(confidence, "low")
    else:
        crown_d = crownmod.crown_diameter_dbh_scaled(result.trunk_diameter_m, height, group)

    # circular projection -> X == Y
    result.crown_diameter_x_m = round(crown_d, 2)
    result.crown_diameter_y_m = round(crown_d, 2)
    base, depth = crownmod.crown_base_and_depth(height, group)
    result.crown_base_height_m = round(base, 2)
    result.crown_depth_m = round(depth, 2)
    result.crown_projected_area_m2 = round(crownmod.crown_projected_area(crown_d), 2)
    cmin, cmax = crownmod.crown_band(crown_d)
    result.crown_min_m = round(cmin, 2)
    result.crown_max_m = round(cmax, 2)

    result.confidence = confidence
    result.warnings = warnings
    return result


def process_many(trees: list[TreeInput], params: ParameterSet) -> list[TreeGeometryResult]:
    """Process a list of inventory records."""
    return [process_tree(t, params) for t in trees]


def _norm(name: str) -> str:
    return " ".join(name.strip().lower().split())
