import pytest

from route_processor.geo import Segment
from route_processor.route_processor import (
    compute_transit_fl,
    compute_toc_wp,
    compute_transit_segments,
    compute_tod_wp,
    compute_llep_wp,
    compute_route_wps,
    process_route,
)


def test_compute_transit_segments(route, config):
    transit_segments = compute_transit_segments(route, config.id_entry)
    assert len(transit_segments) == 2


def test_compute_transit_fl(route, config):
    transit_segments = [
        Segment(route[0], route[1]),
        Segment(route[1], route[2]),
    ]
    transit_fl = compute_transit_fl(transit_segments)

    assert transit_fl == 207


def test_toc_wp(route, config):
    toc_wp = compute_toc_wp(route, config)

    assert toc_wp.Name == "TOC"
    assert toc_wp.Ident == "TOC FL207/3:27"
    assert toc_wp.Type == "USER"
    assert toc_wp.Pos.Lon == pytest.approx(-1.8838, abs=0.0001)
    assert toc_wp.Pos.Lat == pytest.approx(55.3647, abs=0.0001)
    assert toc_wp.Pos.Alt == 20700.0


def test_tod_wp(route, config):
    tod_wp = compute_tod_wp(route, config)

    assert tod_wp.Name == "TOD"
    assert tod_wp.Ident == "TOD FL207/3:27"
    assert tod_wp.Type == "USER"
    assert tod_wp.Pos.Lon == pytest.approx(-2.3207, abs=0.0001)
    assert tod_wp.Pos.Lat == pytest.approx(56.2463, abs=0.0001)
    assert tod_wp.Pos.Alt == 20700.0


def test_llep_wp(route, config):
    llep_wp = compute_llep_wp(route, config)

    assert llep_wp.Name == "LLEP"
    assert llep_wp.Ident == "LLEP 17:18/253"
    assert llep_wp.Type == "USER"
    assert llep_wp.Pos.Lon == pytest.approx(-2.475614, abs=0.0001)
    assert llep_wp.Pos.Lat == pytest.approx(56.70507, abs=0.0001)
    assert llep_wp.Pos.Alt == 500.0


def test_compute_route_wps(route, config):
    route_wps = compute_route_wps(route, config)

    wp1 = route_wps[0]

    assert wp1.Name == "WP1"
    assert wp1.Ident == "2:11/254"
    assert wp1.Type == "USER"
    assert wp1.Pos.Lon == pytest.approx(-2.475614, abs=0.0001)
    assert wp1.Pos.Lat == pytest.approx(56.70507, abs=0.0001)
    assert wp1.Pos.Alt == 500.0


def test_process_route(route, config):
    processed_route_wps = process_route(route, config)
    print()

    for wp in processed_route_wps:
        print(f"{wp.Name} : {wp.Ident}")
