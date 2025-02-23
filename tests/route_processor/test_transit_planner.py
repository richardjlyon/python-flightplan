import pytest

from src.route_processor.transit_planner import (
    _compute_transit_segments,
    TransitBuilder,
)


@pytest.fixture
def transit_builder(route, config):
    transit_segments = _compute_transit_segments(route, config.id_entry)
    departure_bearing_mag = 999
    return TransitBuilder(
        transit_segments,
        config.transit_airspeed_kts,
        config.route_alt_ft,
        departure_bearing_mag,
    )


class TestTransitBuilder:
    def test_start(self, transit_builder):
        transit = transit_builder.set_start().build()
        wp = transit.start_wp

        assert wp.Type == "WAYPOINT"
        assert wp.Name == "Newcastle"
        assert wp.Ident == "0:00/342"
        assert wp.Comment == "START"
        assert wp.Pos.Alt == 266

    def test_toc(self, transit_builder):
        transit = transit_builder.set_toc().build()
        wp = transit.toc_wp

        assert wp.Type == "WAYPOINT"
        assert wp.Name == "TOC"
        assert wp.Ident == "3:48/FL200/TOC"
        assert wp.Pos.Lon == pytest.approx(-1.9625, abs=0.0001)
        assert wp.Pos.Lat == pytest.approx(55.4971, abs=0.0001)
        assert wp.Pos.Alt == 20000

    def test_intermediate_wps(self, transit_builder):
        transit = transit_builder.set_intermediate_wps().build()
        wps = transit.intermediate_wps

        assert len(wps) == 1
        wp = wps[0]
        assert wp.Type == "WAYPOINT"
        assert wp.Name == "Saint Abbs"
        assert wp.Ident == "7:19/350/112.5"
        assert wp.Pos.Lon == pytest.approx(-2.2063, abs=0.0001)
        assert wp.Pos.Lat == pytest.approx(55.9075, abs=0.0001)
        assert wp.Pos.Alt == 20000

    def test_tod(self, transit_builder):
        transit = transit_builder.set_tod().build()
        wp = transit.tod_wp

        assert wp.Type == "WAYPOINT"
        assert wp.Name == "TOD"
        assert wp.Ident == "10:33/FL200/TOD"
        assert wp.Pos.Lon == pytest.approx(-2.3540, abs=0.0001)
        assert wp.Pos.Lat == pytest.approx(56.3449, abs=0.0001)
        assert wp.Pos.Alt == 20000

    def test_end(self, transit_builder):
        transit = transit_builder.set_toc().set_tod().set_end().build()
        wp = transit.end_wp

        assert wp.Type == "WAYPOINT"
        assert wp.Name == "LLEP"
        assert wp.Ident == "13:33/999/LLEP"
        assert wp.Pos.Lon == pytest.approx(-2.4756, abs=0.0001)
        assert wp.Pos.Lat == pytest.approx(56.7051, abs=0.0001)
        assert wp.Pos.Alt == 500


class TestTransitBuilderUtilities:
    def test_flight_level(self, transit_builder):
        assert transit_builder.flight_level == 200
