"""Data models for inputs, parameters and results.

Provenance is tracked explicitly. Each :class:`TreeGeometryResult` field is one
of four kinds, documented in ``docs/data_dictionary.md``:

* **measured**   - supplied by the project (e.g. ``perimeter_cm``);
* **derived**    - computed mathematically (e.g. ``dbh_cm``, ``height_m``);
* **adopted**    - a per-species parameter chosen from literature (H infinity, k);
* **heuristic**  - an engineering assumption not present in the source
  workbook (all crown / DIALux geometry).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["low", "medium", "high"]
CrownMethod = Literal["dbh_scaled", "palm_height_scaled"]


class TreeInput(BaseModel):
    """A single inventory record (minimum required input).

    Only ``perimeter_cm`` is a physical measurement; the names are project
    identification and may be incomplete or taxonomically inconsistent.
    """

    tree_id: str = Field(..., description="Unique tree/unit identifier, e.g. 'UA01'.")
    common_name: str | None = Field(
        None, description="Popular species name as recorded in the project."
    )
    scientific_name: str | None = Field(
        None, description="Scientific name as recorded in the project (may diverge)."
    )
    perimeter_cm: float | None = Field(
        None, description="Measured trunk perimeter in centimetres (at ~1.30 m)."
    )

    model_config = {"extra": "ignore"}


class SpeciesParameters(BaseModel):
    """Adopted (and heuristic) parameters for one species.

    ``height_asymptote_m`` and ``height_shape_k_cm`` are *adopted* parameters
    of the height model. The crown fields are *heuristic* and drive the
    separate crown/DIALux layer.
    """

    common_name: str
    scientific_name: str | None = None
    height_asymptote_m: float = Field(..., description="Adopted asymptotic height H-infinity (m).")
    height_shape_k_cm: float = Field(..., description="Adopted shape parameter k (cm).")
    size_class: str | None = None
    crown_group: str = Field(..., description="Heuristic architectural crown group.")
    crown_method: CrownMethod = "dbh_scaled"
    confidence: Confidence = "medium"
    reference_basis: str | None = None
    limitation: str | None = None
    source_url: str | None = None


class TreeGeometryResult(BaseModel):
    """Full per-tree result: identity + derived height core + heuristic crown."""

    # --- identity (measured / project) ---
    tree_id: str
    common_name: str | None = None
    scientific_name: str | None = None
    perimeter_cm: float | None = None

    # --- height core (derived, reproduces the workbook) ---
    dbh_cm: float | None = None
    trunk_diameter_m: float | None = None
    height_m: float | None = None
    height_min_m: float | None = None
    height_max_m: float | None = None

    # --- crown / DIALux geometry (heuristic) ---
    crown_diameter_x_m: float | None = None
    crown_diameter_y_m: float | None = None
    crown_base_height_m: float | None = None
    crown_depth_m: float | None = None
    crown_projected_area_m2: float | None = None
    crown_min_m: float | None = None
    crown_max_m: float | None = None

    # --- meta ---
    crown_group: str | None = None
    confidence: Confidence = "medium"
    warnings: list[str] = Field(default_factory=list)
