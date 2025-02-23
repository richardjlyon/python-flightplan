"""
Logic for planning the transit phase.
"""

import math
from copy import deepcopy
from typing import List, Tuple, Optional

from src.deserialisers.little_navmap import Waypoint, Pos
from src.route_processor.geo import Segment
from src.route_processor.performance_data import (
    get_climb_descent_performance_data,
    JetOperation,
    ClimbDescentPerformanceData,
)
from src.route_processor.utils import interpolate_lat_lon_flat, mins_secs_str


class Transit:
    """A class for representing a set of transit waypoints."""

    start_wp: Waypoint
    toc_wp: Waypoint
    intermediate_wps: List[Waypoint]
    tod_wp: Waypoint
    end_wp: Waypoint

    def __init__(
        self,
        start_wp: Waypoint,
        toc_wp: Waypoint,
        intermediate_wps: List[Waypoint],
        tod_wp: Waypoint,
        end_wp: Waypoint,
    ):
        self.start_wp = start_wp
        self.toc_wp = toc_wp
        self.intermediate_wps = intermediate_wps
        self.tod_wp = tod_wp
        self.end_wp = end_wp


class TransitBuilder:
    """A class for building a set of transit waypoints from planning data."""

    def __init__(
        self,
        transit_segments: List[Segment],
        transit_groundspeed_kts: int,
        route_alt_ft: int,
        departure_bearing_mag: int,
    ):
        self.transit_segments = transit_segments
        self.transit_groundspeed_kts = transit_groundspeed_kts
        self.route_alt_ft = route_alt_ft
        self.departure_bearing_mag = departure_bearing_mag
        self.flight_level: int
        self.climb_performance_data: Optional[ClimbDescentPerformanceData] = None
        self.descent_performance_data: Optional[ClimbDescentPerformanceData] = None
        self.start_wp: Optional[Waypoint] = None
        self.toc_wp: Optional[Waypoint] = None
        self.intermediate_wps: Optional[List[Waypoint]] = None
        self.tod_wp: Optional[Waypoint] = None
        self.end_wp: Optional[Waypoint] = None

        self._set_flight_level_on_init()

    # -- Public methods -------------------------------------------------------

    def set_start(
        self,
    ) -> "TransitBuilder":
        """
        Start waypoint displays the departure bearing to the next waypoint.
        """
        departure_segment = self.transit_segments[0]
        departure_bearing = round(departure_segment.true_bearing)

        ident = f"0:00/{departure_bearing:03}"

        self.start_wp = deepcopy(departure_segment.start)
        self.start_wp.Type = "WAYPOINT"
        self.start_wp.Ident = ident
        self.start_wp.Comment = "START"

        return self

    def set_toc(self) -> "TransitBuilder":
        """TOC distance is computed from NORMAL_CLIMB distance.
        Time is computed from NORMAL_CLIMB time.
        """

        if self.flight_level is None:
            raise ValueError("Flight level must be set before setting TOC WP")

        ident = f"{mins_secs_str(self.climb_performance_data.time_secs)}/FL{self.flight_level}/TOC"
        pos = self._compute_pos(self.climb_performance_data, self.transit_segments[0])

        self.toc_wp = Waypoint(
            Type="WAYPOINT",
            Name="TOC",
            Ident=ident,
            Comment="TOC",
            Pos=pos,
        )

        return self

    def set_intermediate_wps(self) -> "TransitBuilder":
        """Compute the intermediate waypoints."""
        # TODO Validate initial conditions

        intermediate_wps = []
        cum_time_secs = 0

        for idx, (this_segment, next_segment) in enumerate(
            zip(self.transit_segments, self.transit_segments[1:])
        ):
            has_climb = idx == 0
            transit_wp, segment_time_secs = self._compute_intermediate_waypoint(
                has_climb,
                this_segment,
                next_segment,
                cum_time_secs,
            )
            intermediate_wps.append(transit_wp)
            cum_time_secs += segment_time_secs

        self.intermediate_wps = deepcopy(intermediate_wps)

        return self

    def set_tod(self) -> "TransitBuilder":
        """
        TOD distance is computed from NAV_DESCENT distance.
        Time is computed as the total transit time less the sum of the NAV_DESCENT time
        and NORMAL_CLIMB time.
        """
        if self.flight_level is None:
            raise ValueError("Flight level must be set before setting TOD WP")

        tod_time_secs = self._compute_tod_time_secs()

        pos = self._compute_pos(
            self.descent_performance_data, self.transit_segments[-1]
        )

        ident = f"{mins_secs_str(tod_time_secs)}/FL{self.flight_level}/TOD"

        self.tod_wp = Waypoint(
            Type="WAYPOINT",
            Name="TOD",
            Ident=ident,
            Comment="TOD",
            Pos=pos,
        )

        return self

    def set_end(self) -> "TransitBuilder":
        if self.descent_performance_data is None:
            raise ValueError("FL must be set before setting END WP")

        segment = self.transit_segments[-1]

        tod_time_secs = self._compute_tod_time_secs()
        descent_time_secs = self.descent_performance_data.time_secs
        transit_time_secs = tod_time_secs + descent_time_secs

        ident = (
            f"{mins_secs_str(transit_time_secs)}/{self.departure_bearing_mag:03}/LLEP"
        )

        wp = deepcopy(segment.end)
        wp.Type = "WAYPOINT"
        wp.Name = "LLEP"
        wp.Ident = ident
        wp.Comment = "LLEP"
        wp.Pos.Alt = self.route_alt_ft

        self.end_wp = wp

        return self

    def build(self) -> Transit:
        return Transit(
            start_wp=self.start_wp,
            toc_wp=self.toc_wp,
            intermediate_wps=self.intermediate_wps,
            tod_wp=self.tod_wp,
            end_wp=self.end_wp,
        )

    # -- Private methods --------------------------------------------------------

    def _set_flight_level_on_init(self) -> "TransitBuilder":
        """
        Flight level is estimated as 2 x transit range
        """
        transit_length = sum(segment.length for segment in self.transit_segments)
        transit_bearing = _compute_transit_bearing(self.transit_segments)

        transit_fl = int(2 * transit_length)

        # Ensure flight level is odd or even based on transit_bearing
        if 0 <= transit_bearing < 180:  # Eastbound (odd FL)
            transit_fl = transit_fl | 1  # Force odd flight level (bitwise OR with 1)
        elif 180 <= transit_bearing < 360:  # Westbound (even FL)
            transit_fl = (
                transit_fl & ~1
            )  # Force even flight level (bitwise AND with bitwise NOT of 1)

        # Convert to an actual FL (round to nearest multiple of 10 and divide by 10)
        self.flight_level = (transit_fl // 10) * 10
        self.climb_performance_data = get_climb_descent_performance_data(
            JetOperation.NORMAL_CLIMB, self.flight_level
        )
        self.descent_performance_data = get_climb_descent_performance_data(
            JetOperation.NAV_DESCENT, self.flight_level
        )

    def _compute_tod_time_secs(self) -> float:
        if self.climb_performance_data is None:
            raise ValueError("FL must be set before setting END WP")
        if self.descent_performance_data is None:
            raise ValueError("FL must be set before setting END WP")

        transit_distance_nm = self._compute_transit_distance_nm() - (
            self.climb_performance_data.distance_nm
            + self.descent_performance_data.distance_nm
        )
        transit_time_secs = 3600 * transit_distance_nm / self.transit_groundspeed_kts
        tod_time_secs = self.climb_performance_data.time_secs + transit_time_secs
        return tod_time_secs

    def _compute_pos(self, performance_data, segment: Segment) -> Pos:
        """Compute the position of the TOC waypoint."""
        if self.flight_level is None:
            raise ValueError("FL must be set before setting END WP")

        percent_of_leg = 1.0 - performance_data.distance_nm / segment.length
        lat, lon = interpolate_lat_lon_flat(segment, percent_of_leg)
        alt = int(self.flight_level * 100.0)

        return Pos(**{"@Lon": lon, "@Lat": lat, "@Alt": alt})

    def _compute_transit_distance_nm(self) -> float:
        """Compute the transit distance in nautical miles."""
        return sum(segment.length for segment in self.transit_segments)

    def _compute_intermediate_waypoint(
        self,
        has_climb: bool,
        this_segment: Segment,
        next_segment: Segment,
        cum_time_secs: int,
    ) -> Tuple[Waypoint, int]:
        """
        Compute an intermediate transit waypoint.

        Params:
        - has_climb (bool): True if this is the first segment in the transit sequence.
        - this_segment (Segment): The current segment being evaluated.
        - next_segment (Segment): The subsequent segment used to compute the departure bearing.
        - cum_time_secs (int): The cumulative elapsed time in seconds up to this segment.

        Returns:
        - Tuple[Waypoint, int]: A tuple containing the computed waypoint and the travel time of the segment in seconds.
        """

        departure_bearing = round(next_segment.true_bearing)

        # If this segment has a climb section, account for it in the duration calculation
        if has_climb:
            cruise_distance_nm = (
                this_segment.length - self.climb_performance_data.distance_nm
            )
            cruise_time_secs = 3600 * cruise_distance_nm / self.transit_groundspeed_kts
            climb_time_secs = self.climb_performance_data.time_secs
            segment_time_secs = cruise_time_secs + climb_time_secs
        else:
            segment_time_secs = int(
                this_segment.travel_time_secs(self.transit_groundspeed_kts)
            )

        wp = deepcopy(this_segment.end)

        ident = (
            f"{mins_secs_str(cum_time_secs + segment_time_secs)}/{departure_bearing}"
        )
        if wp.Comment is not None:
            ident += f"/{wp.Comment}"

        wp.Type = "WAYPOINT"
        wp.Ident = ident
        wp.Pos.Alt = self.flight_level * 100

        return wp, segment_time_secs


def _compute_transit_segments(route: List[Waypoint], id_entry: int) -> List[Segment]:
    """Compute the transit segments from the waypoints and config data"""
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
