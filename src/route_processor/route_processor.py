"""
This module analyses a list of waypoints,
inserts TOC and BOD waypoints,
and renames all waypoints to reflect arrival times and departure bearings
"""

from copy import deepcopy
from typing import List

from src.deserialisers.little_navmap import Waypoint
from src.route_processor.geo import Segment
from src.route_processor.processor_config import ProcessorConfig
from src.route_processor.transit_planner import (
    _compute_transit_segments,
    TransitBuilder,
)
from src.route_processor.utils import mins_secs_str


# --Public methods-----------------------------------------------------------------


def process_route(route: List[Waypoint], config: ProcessorConfig) -> List[Waypoint]:
    """Add TOC/TOD waypoints and update WP Idents with nav info."""
    processed_wps = []

    # Transit WPs

    route_segments = _compute_route_segments(route, config)
    departure_bearing_mag = route_segments[0].magnetic_bearing

    transit_segments = _compute_transit_segments(route, config.id_entry)
    builder = TransitBuilder(
        transit_segments,
        config.transit_groundspeed_kts,
        config.route_alt_ft,
        departure_bearing_mag,
    )

    transit_wps = (
        builder.set_start().set_toc().set_intermediate_wps().set_tod().set_end().build()
    )

    processed_wps.extend(
        [
            transit_wps.start_wp,
            transit_wps.toc_wp,
            *transit_wps.intermediate_wps,
            transit_wps.tod_wp,
            transit_wps.end_wp,
        ]
    )

    # Route WPs

    route_wps = _compute_route_wps(route, config)
    processed_wps.extend(
        [
            element.copy() if isinstance(element, dict) else element
            for element in route_wps
        ]
    )

    return processed_wps


# --Private methods-----------------------------------------------------------------


def _compute_route_wps(
    route: List[Waypoint], config: ProcessorConfig
) -> List[Waypoint]:
    """Compute the route waypoints."""

    route_wps = []
    segments = _compute_route_segments(route, config)
    cum_time_secs = 0
    wp_idx = 1

    for this_segment, next_segment in zip(segments, segments[1:]):
        segment_time_secs = this_segment.travel_time_secs(config.route_airspeed_kts)
        cum_time_secs += segment_time_secs
        departure_brg = next_segment.magnetic_bearing

        wp = deepcopy(this_segment.end)

        ident = f"{mins_secs_str(cum_time_secs)}/{departure_brg:03}"
        if wp.Comment is not None:
            ident += f"/{wp.Comment}"

        wp.Type = "WAYPOINT"
        wp.Ident = ident
        wp.Comment = f"WP{wp_idx}"
        wp.Pos.Alt = config.route_alt_ft

        route_wps.append(wp)
        wp_idx += 1

    return route_wps


def _compute_route_segments(
    route: List[Waypoint], config: ProcessorConfig
) -> List[Segment]:
    """Compute the segments of the route from the config data."""
    segments = []
    start_idx = config.id_entry - 1
    end_idx = (
        config.id_exit
    )  # We go one beyond to allow the departure bearing to be computed

    for i in range(start_idx, end_idx):
        segments.append(Segment(deepcopy(route[i]), deepcopy(route[i + 1])))

    return segments
