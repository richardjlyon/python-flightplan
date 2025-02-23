"""This module creates a military-style low level plan.

It inserts TOC and BOD waypoints, and renames all waypoints to reflect arrival times and departure bearings.
"""

import dataclasses
from copy import deepcopy

from src.deserialisers.little_navmap import Waypoint
from src.route_processor.geo import Segment
from src.route_processor.transit_planner import (
    _compute_transit_segments,
    TransitBuilder,
)
from src.route_processor.utils import mins_secs_str


# --Public methods-----------------------------------------------------------------


@dataclasses.dataclass
class ProcessorConfig:
    """Configuration class for processing flight data.

    This dataclass encapsulates various configuration parameters related to flight
    processing, such as waypoint indices, airspeeds, and route altitude. The attributes
    are primarily used for low-level flight planning and performance calculations.

    Attributes:
        id_entry (int):
            The index for the low-level entry point waypoint.
        id_exit (int):
            The index for the low-level exit point waypoint.
        transit_airspeed_kts (int):
            The average transit airspeed (in knots), typically at Mach 0.75.
        route_airspeed_kts (int):
            The airspeed (in knots) used for the low-level route segment.
        route_alt_ft (int, optional):
            The altitude (in feet) for the low-level route. Defaults to 500 feet.

    Notes:
        - The `id_entry` and `id_exit` parameters are expected to reference waypoint
          indices in the relevant flight planning system or dataset.
        - The `route_alt_ft` parameter defaults to 500 feet but can be adjusted
          based on operational needs.

    Example:
        ```python
        from dataclasses import dataclass

        # Initialize a ProcessorConfig instance
        config = ProcessorConfig(
            id_entry=1,
            id_exit=10,
            transit_airspeed_kts=300,
            route_airspeed_kts=250,
            route_alt_ft=400,  # Custom altitude for low-level route
        )

        print(config)
        # Output: ProcessorConfig(id_entry=1, id_exit=10, transit_airspeed_kts=300,
        #                         route_airspeed_kts=250, route_alt_ft=400)
        ```
    """

    id_entry: int  # Low Level Entry Point waypoint index
    id_exit: int  # Low Level Exit Point waypoint index
    transit_airspeed_kts: int  # Average transit groundspeed @ M0.75
    route_airspeed_kts: int  # Low level route airspeed (knots)
    route_alt_ft: int = 500  # Low Level Route altitude


def process_route(route: list[Waypoint], config: ProcessorConfig) -> list[Waypoint]:
    """Processes a route by generating waypoints for both transit and low-level route segments.

    This function takes a list of waypoints (`route`) and a configuration object (`config`)
    to build a comprehensive list of waypoints that include transit and route-specific
    segments. It uses external methods and helpers to compute the corresponding segments
    and integrates them into a final list of processed waypoints.

    Args:
        route (list[Waypoint]):
            A list of waypoints representing the initial flight route.
            Each waypoint contains location and other flight-related data.
        config (ProcessorConfig):
            A configuration object that provides the parameters necessary
            for transit and route segment computations, such as airspeeds,
            altitudes, and waypoint indices.

    Returns:
        list[Waypoint]:
            A list of processed waypoints that include both transit and
            route-specific segments. The waypoints are ordered sequentially
            from the departure point to the final route exit point.

    Process:
        1. **Transit Waypoints:**
           - Compute transit route segments using `_compute_route_segments`, which determines key route-related properties like bearings.
           - Extract `departure_bearing_mag` from the first segment for transit calculations.
           - Compute transit segments up to the entry waypoint using `_compute_transit_segments`, based on the entry configuration (`id_entry`).
           - Use a `TransitBuilder` to generate the transit waypoints, including:
             - Start waypoint
             - Top-of-climb (TOC) waypoint
             - Intermediate waypoints
             - Top-of-descent (TOD) waypoint
             - End waypoint
           - Add transit waypoints to the final list of processed waypoints.

        2. **Route Waypoints:**
           - Compute waypoints specific to the low-level route using `_compute_route_wps` and the configuration object.
           - Copy or retain route waypoints during processing, depending on the type of waypoint (dictionary or object).
           - Append the route waypoints to the list of processed waypoints.

    Notes:
        - The function relies on several external helper functions (_compute_route_segments,
          _compute_transit_segments, and _compute_route_wps) to handle complex waypoint
          and segment calculations.
        - The `TransitBuilder` class is used to streamline the generation of waypoints
          for the transit segment.

    Example:
        ```python
        from my_module import Waypoint, ProcessorConfig, process_route

        # Define a dummy route and configuration
        route = [
            Waypoint(lat=50.0, lon=-0.5),
            Waypoint(lat=51.0, lon=-1.0),
            Waypoint(lat=52.0, lon=-1.5),
        ]

        config = ProcessorConfig(
            id_entry=0,
            id_exit=2,
            transit_airspeed_kts=300,
            route_airspeed_kts=250,
            route_alt_ft=500,
        )

        # Process the route
        processed_wps = process_route(route, config)
        print(processed_wps)
        # Output: [Waypoint objects for transit and route segments]
        ```

    Dependencies:
        - `_compute_route_segments`, `_compute_transit_segments`, `_compute_route_wps`:
          Helper functions that calculate various route-specific details, such as
          segments and waypoints.
        - `TransitBuilder`: A class for building transit waypoint segments based
          on configurations like speed, altitude, and bearing.

    Raises:
        - This function does not explicitly raise exceptions, but exceptions may
          arise from the helper functions or `TransitBuilder` if the inputs or
          configurations are invalid.
    """
    processed_wps = []

    # Transit WPs

    route_segments = _compute_route_segments(route, config)
    departure_bearing_mag = route_segments[0].magnetic_bearing

    transit_segments = _compute_transit_segments(route, config.id_entry)
    builder = TransitBuilder(
        transit_segments,
        config.transit_airspeed_kts,
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
    route: list[Waypoint], config: ProcessorConfig
) -> list[Waypoint]:
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
    route: list[Waypoint], config: ProcessorConfig
) -> list[Segment]:
    """Compute the segments of the route from the config data."""
    segments = []
    start_idx = config.id_entry - 1
    end_idx = (
        config.id_exit
    )  # We go one beyond to allow the departure bearing to be computed

    for i in range(start_idx, end_idx):
        segments.append(Segment(deepcopy(route[i]), deepcopy(route[i + 1])))

    return segments
