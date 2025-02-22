import pytest

from src.route_processor.performance_data import (
    get_performance_data,
    JetOperation,
    PerformanceData,
)


@pytest.mark.parametrize(
    "operation, fl, expected",
    [
        (
                JetOperation.NORMALCLIMB,
                200,  # No interpolation
                PerformanceData(
                    distance_nm=26.0,
                    time_secs=228,
                    fuel_kg=86.0,
                    operation=JetOperation.NORMALCLIMB,
                ),
        ),
        (
                JetOperation.NORMALCLIMB,
                220,  # Interpolation
                PerformanceData(
                    distance_nm=30.0,
                    time_secs=264,
                    fuel_kg=96.0,
                    operation=JetOperation.NORMALCLIMB,
                ),
        ),
        (
                JetOperation.NAVDESCENT,
                250,  # No interpolation
                PerformanceData(
                    distance_nm=25.0,
                    time_secs=210,
                    fuel_kg=11.0,
                    operation=JetOperation.NAVDESCENT,
                ),
        ),
        (
                JetOperation.NAVDESCENT,
                325,  # Interpolation
                PerformanceData(
                    distance_nm=33.5,
                    time_secs=276,
                    fuel_kg=14.0,
                    operation=JetOperation.NAVDESCENT,
                ),
        ),
    ],
)
def test_normal_climb(operation, fl, expected):
    result = get_performance_data(operation, fl)
    assert result == expected
