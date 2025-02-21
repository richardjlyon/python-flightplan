"""
This module analyses a list of waypoints,
inserts TOC and BOD waypoints,
and renames all waypoints to reflect arrival times and departure bearings
"""

import dataclasses
import math
from copy import deepcopy
from typing import List, Tuple

from deserialisers.little_navmap import Waypoint, Pos
from route_processor.geo import Segment


@dataclasses.dataclass
class ProcessorConfig:
    id_entry: int = 3  # Low Level Entry Point waypoint index
    id_exit: int = 12  # Low Level Exit Point waypoint index
    climb_rate_ft_min: int = 6000  # Transit climb rate
    descent_rate_ft_min: int = 6000  # Transit descent rate
    transit_groundspeed_kts: int = 360  # Average transit groundspeed
    route_airspeed_kts: int = 420  # Target route airspeed
    route_alt_ft: int = 500  # Low Level Route altitude


def process_route(route: List[Waypoint], config: ProcessorConfig) -> List[Waypoint]:
    """Add TOC/TOD waypoints and update WP Idents with nav info."""
    processed_wps = []

    # Departure WP
    start_wp = compute_start_wp(route)
    processed_wps.append(start_wp)

    # TOC WP
    toc_wp = compute_toc_wp(route, config)
    processed_wps.append(toc_wp)

    # Transit
    transit_segments = _compute_transit_segments(route, config.id_entry)
    cum_transit_time_secs = 0

    if len(transit_segments) == 1:
        segment = Segment(route[0], route[1])
        cum_transit_time_secs = int(
            segment.travel_time_secs(config.transit_groundspeed_kts)
        )
    else:
        # Intermediate transit WPs
        transit_fl = _compute_transit_fl(transit_segments)
        tp_idx = 1
        for current_segment, next_segment in zip(
            transit_segments, transit_segments[1:]
        ):
            transit_wp, segment_time_secs = compute_intermediate_transit_wp(
                current_segment,
                next_segment,
                transit_fl,
                tp_idx,
                config.transit_groundspeed_kts,
                cum_transit_time_secs,
            )
            processed_wps.append(transit_wp)

            cum_transit_time_secs += segment_time_secs
            tp_idx += 1

    # TOD WP
    tod_wp = compute_tod_wp(route, cum_transit_time_secs, config)
    processed_wps.append(tod_wp)

    # LLEP WP
    llep_wp = compute_llep_wp(route, config)
    processed_wps.append(llep_wp)

    # Route WPs
    route_wps = compute_route_wps(route, config)
    processed_wps.extend(
        [
            element.copy() if isinstance(element, dict) else element
            for element in route_wps
        ]
    )

    return processed_wps


def compute_start_wp(route: List[Waypoint]) -> Waypoint:
    """Compute the start waypoint of the route."""
    start_wp = deepcopy(route[0])
    next_wp = deepcopy(route[1])
    departure_segment = Segment(start_wp, next_wp)

    departure_bearing = round(departure_segment.true_bearing)

    ident = f"0:00/{departure_bearing:03}"

    start_wp.Type = "WAYPOINT"
    start_wp.Ident = ident
    start_wp.Comment = "START"
    start_wp.Pos.Alt = start_wp.Pos.Alt

    return start_wp


def compute_toc_wp(route: List[Waypoint], config: ProcessorConfig) -> Waypoint:
    """Compute the waypoint of the Top Of Climb"""

    transit_segments = _compute_transit_segments(route, config.id_entry)
    transit_fl = _compute_transit_fl(transit_segments)
    time_to_toc_secs = 60 * transit_fl * 100 / config.climb_rate_ft_min
    distance_to_toc_nm = time_to_toc_secs * config.transit_groundspeed_kts / 3600

    climb_segment = transit_segments[0]
    percent_of_leg = distance_to_toc_nm / climb_segment.length
    lat, lon = _interpolate_lat_lon_flat(climb_segment, percent_of_leg)
    alt = int(transit_fl * 100.0)

    ident = f"{_mins_secs_str(time_to_toc_secs)}/FL{transit_fl}/TOC"

    return Waypoint(
        Type="WAYPOINT",
        Name="TOC",
        Ident=ident,
        Comment="TOC",
        Pos=Pos(**{"@Lon": lon, "@Lat": lat, "@Alt": alt}),
    )


def compute_intermediate_transit_wp(
    current_segment: Segment,
    next_segment: Segment,
    transit_fl: int,
    wp_idx: int,
    groundspeed_kts: int,
    cum_time_secs: int,
) -> Tuple[Waypoint, int]:
    """Compute an intermediate transit waypoint."""

    departure_bearing = round(next_segment.true_bearing)
    segment_time_secs = current_segment.travel_time_secs(groundspeed_kts)

    wp = deepcopy(current_segment.end)

    ident = f"{_mins_secs_str(cum_time_secs + segment_time_secs)}/{departure_bearing}"
    if wp.Comment is not None:
        ident += f"/{wp.Comment}"

    wp.Type = "WAYPOINT"
    wp.Ident = ident
    wp.Comment = f"TP{wp_idx}"
    wp.Pos.Alt = transit_fl * 100

    return wp, segment_time_secs


def compute_tod_wp(
    route: List[Waypoint], cum_transit_time_secs: int, config: ProcessorConfig
) -> Waypoint:
    """Compute the waypoint of the Top Of Descent"""

    # Compute descent time and distance
    transit_segments = _compute_transit_segments(route, config.id_entry)
    transit_fl = _compute_transit_fl(transit_segments)
    time_to_descend_secs = 60 * transit_fl * 100 / config.descent_rate_ft_min
    distance_to_descend_nm = (
        time_to_descend_secs * config.transit_groundspeed_kts / 3600
    )

    # Compute TOD lat/lon
    descent_segment = transit_segments[-1]
    percent_of_leg = distance_to_descend_nm / descent_segment.length
    lat, lon = _interpolate_lat_lon_flat(descent_segment, percent_of_leg)
    alt = transit_fl * 100

    # Compute TOD time
    # This is (segment_duration_secs - time_to_descend_secs) + cum_time_secs
    segment_duration_secs = descent_segment.travel_time_secs(
        config.transit_groundspeed_kts
    )
    tod_secs = segment_duration_secs - time_to_descend_secs + cum_transit_time_secs

    ident = f"{_mins_secs_str(tod_secs)}/FL{transit_fl}/TOD"

    return Waypoint(
        Type="WAYPOINT",
        Name="TOD",
        Ident=ident,
        Comment="TOD",
        Pos=Pos(**{"@Lon": lon, "@Lat": lat, "@Alt": alt}),
    )


def compute_llep_wp(route: List[Waypoint], config: ProcessorConfig) -> Waypoint:
    """Compute the waypoint of the Low Level Entry Point"""

    idx_entry = config.id_entry - 1
    segment = Segment(deepcopy(route[idx_entry]), deepcopy(route[idx_entry + 1]))
    departure_brg = segment.magnetic_bearing

    # Compute the arrival time from the transit segments
    transit_segments = _compute_transit_segments(route, config.id_entry)
    transit_distance_nm = sum(segment.length for segment in transit_segments)
    transit_time_secs = 3600 * transit_distance_nm / config.transit_groundspeed_kts

    llep_wp = deepcopy(route[idx_entry])

    ident = f"{_mins_secs_str(transit_time_secs)}/{departure_brg:03}/LLEP"
    if llep_wp.Comment is not None:
        ident += f"/{llep_wp.Comment}"

    llep_wp.Type = "WAYPOINT"
    llep_wp.Ident = ident
    llep_wp.Comment = "LLEP"
    llep_wp.Pos.Alt = config.route_alt_ft

    return llep_wp


def compute_route_wps(route: List[Waypoint], config: ProcessorConfig) -> List[Waypoint]:
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

        ident = f"{_mins_secs_str(cum_time_secs)}/{departure_brg:03}"
        if wp.Comment is not None:
            ident += f"/{wp.Comment}"

        wp.Type = "WAYPOINT"
        wp.Ident = ident
        wp.Comment = f"WP{wp_idx}"
        wp.Pos.Alt = config.route_alt_ft

        route_wps.append(wp)
        wp_idx += 1

    return route_wps


def _compute_transit_segments(route: List[Waypoint], id_entry: int) -> List[Segment]:
    """Compute the segments of the climb from the config data"""
    idx_entry = id_entry - 1

    if idx_entry < 0 or idx_entry >= len(route):
        raise ValueError("entry id must be between 0 and the number of waypoints")

    segments = []
    for i in range(0, idx_entry):
        segments.append(Segment(deepcopy(route[i]), deepcopy(route[i + 1])))

    return segments


def _compute_transit_fl(transit_segments: List[Segment]) -> int:
    """Compute the transit flight level for the given transit segments."""
    transit_length = sum(segment.length for segment in transit_segments)
    transit_bearing = _compute_transit_bearing(transit_segments)

    transit_fl = int(2 * transit_length)

    # Ensure flight level is odd or even based on transit_bearing
    if 0 <= transit_bearing < 180:  # Eastbound (odd FL)
        transit_fl = transit_fl | 1  # Force odd flight level (bitwise OR with 1)
    elif 180 <= transit_bearing < 360:  # Westbound (even FL)
        transit_fl = (
            transit_fl & ~1
        )  # Force even flight level (bitwise AND with bitwise NOT of 1)

    # Convert to an actual FL (round to nearest multiple of 10 and divide by 10)
    transit_fl = (transit_fl // 10) * 10

    return transit_fl


def _compute_transit_bearing(transit_segments: List[Segment]) -> int:
    """Compute the transit bearing for the given transit segments."""
    x = sum(
        math.cos(math.radians(segment.true_bearing)) for segment in transit_segments
    )
    y = sum(
        math.sin(math.radians(segment.true_bearing)) for segment in transit_segments
    )

    return int(math.degrees(math.atan2(y, x)) % 360)


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


def _interpolate_lat_lon_flat(segment: Segment, percent):
    """
    Compute the latitude and longitude of a point at a percentage along a flat-Earth segment.

    :param segment: The segment to interpolate along
    :param percent: Fraction (0.0 to 1.0) of the distance along the segment
    :return: (lat, lon) tuple of the interpolated point in degrees
    """
    if not 0.0 <= percent <= 1.0:
        raise ValueError("Percent argument must be between 0.0 and 1.0")

    lat1 = segment.start.Pos.Lat
    lat2 = segment.end.Pos.Lat
    lon1 = segment.start.Pos.Lon
    lon2 = segment.end.Pos.Lon

    # Linear interpolation
    lat = lat1 + percent * (lat2 - lat1)
    lon = lon1 + percent * (lon2 - lon1)

    return lat, lon


def _mins_secs_str(time_in_seconds) -> str:
    """Return mins and seconds as a string from seconds."""
    mins = int(time_in_seconds / 60)
    secs = int(time_in_seconds % 60)

    return f"{mins}:{secs:02}"


def _compute_departure_bearing(route: List[Waypoint], wp_id: int) -> int:
    """Compute the departure bearing of waypoint wp_id."""
    start_wp = route[wp_id]
    end_wp = route[wp_id + 1]
    departure_segment = Segment(start_wp, end_wp)

    return round(departure_segment.true_bearing)
