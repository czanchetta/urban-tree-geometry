"""urban-tree-geometry.

Preliminary estimation of tree height, crown diameter and 3D geometry
parameters for outdoor lighting models (e.g. DIALux) from tree-inventory data.

The package deliberately separates two layers of trust:

* **Height core** (:mod:`urban_tree_geometry.calculations`) faithfully
  reproduces the source workbook and is regression-tested against it.
* **Crown / DIALux geometry** (:mod:`urban_tree_geometry.crown`) is an
  explicitly labelled engineering *heuristic*; it is not derived from, nor
  validated against, the workbook.

This tool produces preliminary estimates for lighting pre-modelling only. It
does not replace a field dendrometric survey, forest inventory, arboricultural
report, stability assessment or topographic survey.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .models import SpeciesParameters, TreeGeometryResult, TreeInput
from .parameters import (
    CrownGroup,
    ParameterSet,
    load_parameter_set,
    load_parameter_set_json,
)

__all__ = [
    "TreeInput",
    "SpeciesParameters",
    "TreeGeometryResult",
    "CrownGroup",
    "ParameterSet",
    "load_parameter_set",
    "load_parameter_set_json",
    "__version__",
]
