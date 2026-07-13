"""Load and manage externalised parameters.

Parameters live in data files (CSV by default; YAML/JSON also accepted), never
hard-coded in the calculation modules. Users may override the parameter set by
pointing at their own files or by mutating the loaded :class:`ParameterSet`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

from .models import SpeciesParameters

# Default location of the packaged parameter files (repository ``data/parameters``).
_DEFAULT_DIR = Path(__file__).resolve().parents[2] / "data" / "parameters"

# Shared single-source-of-truth JSON, loaded by BOTH the Python package and the
# TypeScript frontend (repository ``data/species_parameters.json``).
_SHARED_JSON = Path(__file__).resolve().parents[2] / "data" / "species_parameters.json"


@dataclass(frozen=True)
class CrownGroup:
    """Heuristic architectural crown group.

    All values are engineering parameters derived from general literature and
    adjusted by crown architecture. They are NOT species-specific published
    dendrometric coefficients.
    """

    crown_group: str
    crown_dbh_factor: float
    crown_height_limit_fraction: float
    crown_depth_fraction: float
    crown_method: str
    description: str = ""


@dataclass
class PalmRule:
    """Heuristic palm crown rule (crown scales with height, not DBH)."""

    palm_crown_height_factor: float = 0.35
    palm_crown_min_m: float = 3.5
    palm_crown_max_m: float = 6.0


@dataclass
class ParameterSet:
    """A complete, overridable set of parameters used by the pipeline."""

    species: dict[str, SpeciesParameters] = field(default_factory=dict)
    crown_groups: dict[str, CrownGroup] = field(default_factory=dict)
    palm_rule: PalmRule = field(default_factory=PalmRule)

    def get_species(self, common_name: str | None) -> SpeciesParameters | None:
        """Return parameters for a species by common name (case-insensitive)."""
        if common_name is None:
            return None
        key = common_name.strip().upper()
        return self.species.get(key)

    def get_crown_group(self, group: str) -> CrownGroup | None:
        return self.crown_groups.get(group)


def _read_table(path: Path) -> list[dict]:
    """Read a CSV/YAML/JSON parameter table into a list of row dicts."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path).to_dict(orient="records")
    if suffix in {".yaml", ".yml"}:
        return list(yaml.safe_load(path.read_text(encoding="utf-8")))
    if suffix == ".json":
        return list(json.loads(path.read_text(encoding="utf-8")))
    raise ValueError(f"Unsupported parameter file type: {path.suffix}")


def load_parameter_set(
    species_path: Path | None = None,
    crown_path: Path | None = None,
    palm_path: Path | None = None,
    base_dir: Path | None = None,
) -> ParameterSet:
    """Load parameters from data files.

    Args:
        species_path: species parameter file (defaults to packaged CSV).
        crown_path: crown-group parameter file (defaults to packaged CSV).
        palm_path: palm-rule parameter file (defaults to packaged CSV).
        base_dir: directory to resolve the default file names against.

    Returns:
        A populated :class:`ParameterSet`.
    """
    # Prefer the shared single-source-of-truth JSON when no explicit paths are
    # given and it is present. This is the same file the TypeScript frontend
    # loads, guaranteeing the two implementations use identical parameters.
    if species_path is None and crown_path is None and palm_path is None:
        shared = (Path(base_dir) / "species_parameters.json") if base_dir else _SHARED_JSON
        if shared.is_file():
            return load_parameter_set_json(shared)

    base = base_dir or _DEFAULT_DIR
    species_path = Path(species_path) if species_path else base / "species_parameters.csv"
    crown_path = Path(crown_path) if crown_path else base / "crown_parameters.csv"
    palm_path = Path(palm_path) if palm_path else base / "palm_rule.csv"

    species: dict[str, SpeciesParameters] = {}
    for row in _read_table(species_path):
        sp = SpeciesParameters(**{k: _clean(v) for k, v in row.items()})
        species[sp.common_name.strip().upper()] = sp

    crown_groups: dict[str, CrownGroup] = {}
    for row in _read_table(crown_path):
        cg = CrownGroup(
            crown_group=str(row["crown_group"]),
            crown_dbh_factor=float(row["crown_dbh_factor"]),
            crown_height_limit_fraction=float(row["crown_height_limit_fraction"]),
            crown_depth_fraction=float(row["crown_depth_fraction"]),
            crown_method=str(row["crown_method"]),
            description=str(row.get("description", "")),
        )
        crown_groups[cg.crown_group] = cg

    palm_kwargs = {str(r["parameter"]): float(r["value"]) for r in _read_table(palm_path)}
    palm_rule = PalmRule(**palm_kwargs)

    return ParameterSet(species=species, crown_groups=crown_groups, palm_rule=palm_rule)


def load_parameter_set_json(path: Path | None = None) -> ParameterSet:
    """Load the shared single-source-of-truth JSON parameter document.

    This is the same file consumed by the TypeScript frontend
    (``data/species_parameters.json``). It contains species, crown groups and
    the palm rule in one document, so both implementations stay in lockstep.
    """
    path = Path(path) if path else _SHARED_JSON
    doc = json.loads(path.read_text(encoding="utf-8"))

    species: dict[str, SpeciesParameters] = {}
    for row in doc["species"]:
        sp = SpeciesParameters(**{k: _clean(v) for k, v in row.items()})
        species[sp.common_name.strip().upper()] = sp

    crown_groups: dict[str, CrownGroup] = {}
    for name, row in doc["crown_groups"].items():
        crown_groups[name] = CrownGroup(
            crown_group=name,
            crown_dbh_factor=float(row["crown_dbh_factor"]),
            crown_height_limit_fraction=float(row["crown_height_limit_fraction"]),
            crown_depth_fraction=float(row["crown_depth_fraction"]),
            crown_method=str(row["crown_method"]),
            description=str(row.get("description") or ""),
        )

    palm_rule = PalmRule(**{k: float(v) for k, v in doc["palm_rule"].items()})
    return ParameterSet(species=species, crown_groups=crown_groups, palm_rule=palm_rule)


def _clean(value):
    """Convert pandas NaN to None."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
