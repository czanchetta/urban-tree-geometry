"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from urban_tree_geometry.parameters import load_parameter_set

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def params():
    """The packaged default parameter set."""
    return load_parameter_set()
