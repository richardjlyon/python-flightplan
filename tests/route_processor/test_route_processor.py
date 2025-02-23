"""Route processor tests."""

import pytest

from src.route_processor.route_processor import (
    _compute_route_segments,
    _compute_route_wps,
)


class TestProcessedRoute:
    """Processed route tests."""

    def test_process_route(self, processed_route):
        """Tests that the route processor generates the expected number of waypoints."""
        assert len(processed_route) == 14

    @pytest.mark.parametrize(
        ("index", "expected"),
        [
            (5, {"Comment": "WP1", "Name": "Forfar", "Ident": "2:11/338"}),
            (
                6,
                {
                    "Comment": "WP2",
                    "Name": "Crathie",
                    "Ident": "5:56/251",
                },
            ),
            (
                7,
                {
                    "Comment": "WP3",
                    "Name": "Braemar",
                    "Ident": "7:16/225",
                },
            ),
            (
                12,
                {
                    "Comment": "WP8",
                    "Name": "Fort Augustus",
                    "Ident": "17:49/033",
                },
            ),
            (
                13,
                {
                    "Comment": "WP9",
                    "Name": None,
                    "Ident": "20:42/049/ILS108.5/RW05",
                },
            ),
        ],
    )
    def test_compute_route_wps(self, processed_route, index, expected):
        """Tests that the route processor generates the expected waypoints."""
        wp = processed_route[index]

        assert wp.Name == expected["Name"]
        assert wp.Ident == expected["Ident"]
        assert wp.Comment == expected["Comment"]


class TestRouteProcessingUtilities:
    """Route processing utilities tests."""

    def test_compute_route_segments(self, route, config):
        """Tests that it generates the expected number of route segments."""
        route_segments = _compute_route_segments(route, config)
        assert len(route_segments) == 10

    def test_compute_route_wps(self, route, config):
        """Tests that it generates the expected number of route waypoints."""
        route_wps = _compute_route_wps(route, config)
        assert len(route_wps) == 9
