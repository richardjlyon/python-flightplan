"""Performance data tests."""

import pytest

from src.route_processor.performance_data import (
    get_climb_descent_performance_data,
    JetOperation,
    ClimbDescentPerformanceData,
    get_ll_cruise_performance_data,
    LLCruisePerformanceData,
    get_ml_cruise_performance_data,
    MLCruisePerformanceData,
)


@pytest.mark.parametrize(
    "operation, fl, expected",
    [
        (
            JetOperation.NORMAL_CLIMB,
            200,  # No interpolation
            ClimbDescentPerformanceData(
                distance_nm=26.0,
                time_secs=228,
                fuel_kg=86.0,
                operation=JetOperation.NORMAL_CLIMB,
            ),
        ),
        (
            JetOperation.NORMAL_CLIMB,
            220,  # Interpolation
            ClimbDescentPerformanceData(
                distance_nm=30.0,
                time_secs=264,
                fuel_kg=96.0,
                operation=JetOperation.NORMAL_CLIMB,
            ),
        ),
        (
            JetOperation.NAV_DESCENT,
            250,  # No interpolation
            ClimbDescentPerformanceData(
                distance_nm=25.0,
                time_secs=210,
                fuel_kg=11.0,
                operation=JetOperation.NAV_DESCENT,
            ),
        ),
        (
            JetOperation.NAV_DESCENT,
            325,  # Interpolation
            ClimbDescentPerformanceData(
                distance_nm=33.5,
                time_secs=276,
                fuel_kg=14.0,
                operation=JetOperation.NAV_DESCENT,
            ),
        ),
    ],
)
def test_climb_descent(operation, fl, expected):
    """Tests that the climb descent performance data is computed correctly."""
    result = get_climb_descent_performance_data(operation, fl)
    assert result == expected


@pytest.mark.parametrize(
    "operation, kts, expected",
    [
        (
            JetOperation.LL_CRUISE,
            420,
            LLCruisePerformanceData(
                kg_min=18.9,
                operation=JetOperation.LL_CRUISE,
            ),
        ),
        (
            JetOperation.LL_CRUISE,
            330,
            LLCruisePerformanceData(
                kg_min=12.1,
                operation=JetOperation.LL_CRUISE,
            ),
        ),
        (
            JetOperation.LL_CRUISE,
            300,
            LLCruisePerformanceData(
                kg_min=10.5,
                operation=JetOperation.LL_CRUISE,
            ),
        ),
    ],
)
def test_ll_cruise(operation, kts, expected):
    """Tests that low level cruise performance data is computed correctly."""
    result = get_ll_cruise_performance_data(operation, kts)
    assert result == expected


@pytest.mark.parametrize(
    "operation, fl, expected",
    [
        (
            JetOperation.ML_CRUISE,
            200,
            MLCruisePerformanceData(
                kg_min=12.2,
                kg_anm=1.59,
                operation=JetOperation.ML_CRUISE,
            ),
        ),
        (
            JetOperation.ML_CRUISE,
            325,
            MLCruisePerformanceData(
                kg_min=7.55,
                kg_anm=1.03,
                operation=JetOperation.ML_CRUISE,
            ),
        ),
    ],
)
def test_ml_cruise(operation, fl, expected):
    """Tests that medium level cruise performance data is computed correctly."""
    result = get_ml_cruise_performance_data(operation, fl)
    assert result == expected
