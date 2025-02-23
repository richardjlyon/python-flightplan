"""Tests for geo.py."""

import pytest


def test_length(montrose_to_forfar):
    """Tests that the length  is accurately calculated."""
    segment = montrose_to_forfar
    assert segment.length == pytest.approx(15.4, abs=0.1)


def test_true_bearing(montrose_to_forfar):
    """Tests that the true bearing of the  segment is correctly calculated."""
    segment = montrose_to_forfar
    assert segment.true_bearing == 254


def test_magnetic_bearing(montrose_to_forfar):
    """Tests that the magnetic bearing is correctly calculated."""
    segment = montrose_to_forfar
    assert segment.magnetic_bearing == 253


def test_travel_time(montrose_to_forfar):
    """Tests that the travel time is correctly calculated."""
    segment = montrose_to_forfar
    travel_time = segment.travel_time_secs(420)
    assert travel_time == pytest.approx(132, abs=1)
