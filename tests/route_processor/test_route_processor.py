import pytest

from src.route_processor.route_processor import (
    _compute_transit_segments,
    _compute_transit_fl,
    _compute_route_segments,
    compute_route_wps,
)


class TestProcessedRoute:
    def test_process_route(self, processed_route):
        assert len(processed_route) == 14

    def test_start_wp(self, processed_route):
        start_wp = processed_route[0]

        assert start_wp.Type == "WAYPOINT"
        assert start_wp.Name == "Newcastle"
        assert start_wp.Ident == "0:00/342"
        assert start_wp.Comment == "START"
        assert start_wp.Pos.Alt == 266

    def test_toc_wp(self, processed_route):
        toc_wp = processed_route[1]

        assert toc_wp.Type == "WAYPOINT"
        assert toc_wp.Name == "TOC"
        assert toc_wp.Ident == "3:20/FL200/TOC"
        assert toc_wp.Pos.Lon == pytest.approx(-1.8772, abs=0.0001)
        assert toc_wp.Pos.Lat == pytest.approx(55.3537, abs=0.0001)
        assert toc_wp.Pos.Alt == 20000

    def test_transit(self, processed_route):
        wp = processed_route[2]

        assert wp.Type == "WAYPOINT"
        assert wp.Name == "Saint Abbs"
        assert wp.Ident == "9:10/350/112.5"
        assert wp.Pos.Lon == pytest.approx(-2.2063, abs=0.0001)
        assert wp.Pos.Lat == pytest.approx(55.9075, abs=0.0001)
        assert wp.Pos.Alt == 20000

    def test_tod_wp(self, processed_route):
        tod_wp = processed_route[3]

        assert tod_wp.Type == "WAYPOINT"
        assert tod_wp.Name == "TOD"
        assert tod_wp.Ident == "13:58/FL200/TOD"
        assert tod_wp.Pos.Lon == pytest.approx(-2.3169, abs=0.0001)
        assert tod_wp.Pos.Lat == pytest.approx(56.2349, abs=0.0001)
        assert tod_wp.Pos.Alt == 20000

    def test_llep_wp(self, processed_route):
        llep_wp = processed_route[4]

        assert llep_wp.Type == "WAYPOINT"
        assert llep_wp.Name == "Montrose"
        assert llep_wp.Ident == "17:18/253/LLEP"
        assert llep_wp.Pos.Lon == pytest.approx(-2.475614, abs=0.0001)
        assert llep_wp.Pos.Lat == pytest.approx(56.70507, abs=0.0001)
        assert llep_wp.Pos.Alt == 500

    @pytest.mark.parametrize(
        "index, expected",
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
        wp = processed_route[index]

        assert wp.Name == expected["Name"]
        assert wp.Ident == expected["Ident"]
        assert wp.Comment == expected["Comment"]


class TestRouteProcessingUtilities:
    def test_compute_transit_segments(self, route, config):
        transit_segments = _compute_transit_segments(route, config.id_entry)
        assert len(transit_segments) == 2

    def test_compute_transit_fl(self, route, config):
        transit_segments = _compute_transit_segments(route, config.id_entry)
        transit_fl = _compute_transit_fl(transit_segments)

        assert transit_fl == 200

    def test_compute_route_segments(self, route, config):
        route_segments = _compute_route_segments(route, config)
        assert len(route_segments) == 10

    def test_compute_route_wps(self, route, config):
        route_wps = compute_route_wps(route, config)
        assert len(route_wps) == 9
