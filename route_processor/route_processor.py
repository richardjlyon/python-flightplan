"""
This module analyses a list of waypoints,
inserts TOC and BOD waypoints,
and renames all waypoints to reflect arrival times and departure bearings
"""

import copy
import dataclasses
from typing import List

from deserialisers.little_navmap import Waypoint, Pos
from route_processor.geo import Segment


@dataclasses.dataclass
class ProcessorConfig:
    id_entry: int = 1  # Low Level Entry Point waypoint index
    id_exit: int = -1  # Low Level Exit Point waypoint index
    climb_rate_ft_min: int = 6000  # Transit climb rate
    descent_rate_ft_min: int = 6000  # Transit descent rate
    climb_goundspeed_kts: int = 360  # Transit climb groundspeed
    descent_goundspeed_kts: int = 360  # Transit climb groundspeed
    transit_groundspeed_kts: int = 360  # Average transit groundspeed
    route_airspeed_kts: int = 420  # Target route airspeed
    route_alt_ft: int = 500  # Low Level Route altitude


def process_route(route: List[Waypoint], config: ProcessorConfig) -> List[Waypoint]:
    processed_wps = []

    # Start at airfield
    start_wp = route[0]
    start_wp.Name = "WP0"
    processed_wps.append(start_wp)

    # TOC
    toc_wp = compute_toc_wp(route, config)
    processed_wps.append(toc_wp)

    # Intermediate transit wps
    transit_segments = compute_transit_segments(route, config.id_entry)
    if len(transit_segments) > 1:
        transit_fl = compute_transit_fl(transit_segments)
        tp_idx = 1
        for segment in transit_segments[:-1]:
            wp = segment.end
            wp.Name = f"TP{tp_idx}"
            wp.Pos.Alt = transit_fl
            processed_wps.append(wp)

            tp_idx += 1

    # TOD
    tod_wp = compute_tod_wp(route, config)
    processed_wps.append(tod_wp)

    # LLEP
    llep_wp = compute_llep_wp(route, config)
    processed_wps.append(llep_wp)

    # Route WPs
    route_wps = compute_route_wps(route, config)
    processed_wps.extend(route_wps)

    return processed_wps


def compute_transit_segments(route: List[Waypoint], id_entry: int) -> List[Segment]:
    """Compute the segments of the climb from the config data"""
    if id_entry < 0 or id_entry >= len(route):
        raise ValueError("entry id must be between 0 and the number of waypoints")

    segments = []
    for i in range(0, id_entry):
        segments.append(Segment(route[i], route[i + 1]))

    return segments


def compute_transit_fl(transit_segments: List[Segment]) -> int:
    """Compute the transit flight level for the given transit segments."""
    transit_length = sum(segment.length for segment in transit_segments)
    transit_fl = int(2 * transit_length)
    # TODO Convert to an actual FL

    return transit_fl


def compute_toc_wp(route: List[Waypoint], config: ProcessorConfig) -> Waypoint:
    """Compute the waypoint of the Top Of Climb"""

    transit_segments = compute_transit_segments(route, config.id_entry)
    transit_fl = compute_transit_fl(transit_segments)
    time_to_toc_secs = 60 * transit_fl * 100 / config.climb_rate_ft_min
    distance_to_toc_nm = time_to_toc_secs * config.climb_goundspeed_kts / 3600

    climb_segment = transit_segments[0]
    percent_of_leg = distance_to_toc_nm / climb_segment.length
    lat, lon = _interpolate_lat_lon_flat(climb_segment, percent_of_leg)
    alt = transit_fl * 100.0
    ident = f"TOC FL{transit_fl}/{_mins_secs_str(time_to_toc_secs)}"

    return Waypoint(
        Name="TOC",
        Ident=ident,
        Type="USER",
        Pos=Pos(**{"@Lon": lon, "@Lat": lat, "@Alt": alt}),
    )


def compute_tod_wp(route: List[Waypoint], config: ProcessorConfig) -> Waypoint:
    """Compute the waypoint of the Top Of Descent"""
    transit_segments = compute_transit_segments(route, config.id_entry)
    transit_fl = compute_transit_fl(transit_segments)
    time_to_descend_secs = 60 * transit_fl * 100 / config.descent_rate_ft_min
    distance_to_descend_nm = time_to_descend_secs * config.descent_goundspeed_kts / 3600

    descent_segment = transit_segments[-1]
    percent_of_leg = distance_to_descend_nm / descent_segment.length
    lat, lon = _interpolate_lat_lon_flat(descent_segment, percent_of_leg)
    alt = transit_fl * 100.0
    ident = f"TOD FL{transit_fl}/{_mins_secs_str(time_to_descend_secs)}"

    return Waypoint(
        Name="TOD",
        Ident=ident,
        Type="USER",
        Pos=Pos(**{"@Lon": lon, "@Lat": lat, "@Alt": alt}),
    )


def compute_llep_wp(route: List[Waypoint], config: ProcessorConfig) -> Waypoint:
    """Compute the waypoint of the Low Level Entry Point"""

    # Compute transit time
    # TODO Uses average transit airspeed. Consider refactoring to accommodate climb/descent config
    transit_segments = compute_transit_segments(route, config.id_entry)
    llep_wp = transit_segments[-1].end
    transit_length = sum(segment.length for segment in transit_segments)
    transit_time_secs = transit_length / config.transit_groundspeed_kts * 3600

    departure_brg = _compute_departure_bearing(route, config.id_entry)

    llep_wp.Name = "LLEP"
    llep_wp.Ident = f"LLEP {_mins_secs_str(transit_time_secs)}/{departure_brg:03}"
    llep_wp.Pos.Alt = config.route_alt_ft

    return llep_wp


def compute_route_wps(route: List[Waypoint], config: ProcessorConfig) -> List[Waypoint]:
    """Compute the route waypoints."""

    route_wps = []
    start_wp_id = config.id_entry
    end_wp_id = len(route) + config.id_exit
    cum_time_secs = 0
    wp_idx = 1

    for wp_id in range(start_wp_id, end_wp_id):
        segment_time_secs = _compute_segment_time_secs(
            route, wp_id, config.route_airspeed_kts
        )
        cum_time_secs += segment_time_secs
        departure_brg = _compute_departure_bearing(route, wp_id)

        wp = copy.deepcopy(route[wp_id])
        wp.Name = f"WP{wp_idx}"
        wp.Ident = f"{_mins_secs_str(cum_time_secs)}/{departure_brg:03}"
        wp.Pos.Alt = config.route_alt_ft
        route_wps.append(wp)

        wp_idx += 1

    return route_wps


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


def _compute_segment_time_secs(
    route: List[Waypoint], wp_id: int, airspeed_kts: int
) -> int:
    """Compute the segment time in seconds of a waypoint wp_id."""
    start_wp = route[wp_id]
    end_wp = route[wp_id + 1]
    segment = Segment(start_wp, end_wp)

    return int(segment.travel_time_secs(airspeed_kts))
