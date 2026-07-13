"""Tests for the asymptotic height model."""

import pytest

from urban_tree_geometry.calculations import UnitError, height_from_dbh, round_to_step


def test_height_positive():
    assert height_from_dbh(30.0, 18.0, 40.0) > 0


def test_height_at_least_breast_height():
    # even a tiny DBH must not fall below 1.30 m
    assert height_from_dbh(0.5, 20.0, 40.0) >= 1.30


def test_height_approaches_asymptote():
    h = height_from_dbh(10_000.0, 25.0, 45.0)
    assert h == pytest.approx(25.0, abs=0.5)


def test_asymptote_too_low_rejected():
    with pytest.raises(ValueError):
        height_from_dbh(30.0, 1.30, 40.0)


def test_k_zero_rejected():
    with pytest.raises(ValueError):
        height_from_dbh(30.0, 18.0, 0.0)


def test_k_negative_rejected():
    with pytest.raises(ValueError):
        height_from_dbh(30.0, 18.0, -5.0)


def test_dbh_nonpositive_rejected():
    with pytest.raises(UnitError):
        height_from_dbh(0.0, 18.0, 40.0)


def test_rounding_half_up():
    assert round_to_step(7.25) == 7.5
    assert round_to_step(7.24) == 7.0
    assert round_to_step(2.0) == 2.0
