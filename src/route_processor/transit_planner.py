"""Logic for planning the transit phase."""

import math
from copy import deepcopy

from src.deserialisers.little_navmap import Pos, Waypoint
from src.route_processor.geo import Segment
from src.route_processor.performance_data import (
    ClimbDescentPerformanceData,
    JetOperation,
    get_climb_descent_performance_data,
)
from src.route_processor.utils import interpolate_lat_lon_flat, mins_secs_str


class Transit:
    """Represents a transit segment of a flight route.

    The `Transit` class encapsulates the waypoints associated with the transit phase of a flight,
    including the start and end waypoints, top-of-climb (TOC), top-of-descent (TOD), and any
    intermediate waypoints.

    Attributes:
        start_wp (Waypoint):
            The waypoint marking the beginning of the transit segment.
        toc_wp (Waypoint):
            The waypoint representing the top-of-climb (TOC) point.
        intermediate_wps (list[Waypoint]):
            A list of waypoints specifying the intermediate positions between
            the TOC and TOD waypoints.
        tod_wp (Waypoint):
            The waypoint representing the top-of-descent (TOD) point.
        end_wp (Waypoint):
            The waypoint marking the end of the transit segment.

    Methods:
        __init__(self, start_wp, toc_wp, intermediate_wps, tod_wp, end_wp):
            Initializes a `Transit` object with the specified waypoints for the transit
            segment.

    Example:
        ```python
        from my_module import Waypoint, Transit

        # Define waypoints
        start = Waypoint(lat=50.0, lon=-0.5)
        toc = Waypoint(lat=51.0, lon=-0.8)
        intermediate = [Waypoint(lat=51.5, lon=-1.0), Waypoint(lat=52.0, lon=-1.2)]
        tod = Waypoint(lat=52.5, lon=-1.4)
        end = Waypoint(lat=53.0, lon=-1.6)

        # Create a Transit object
        transit_segment = Transit(start, toc, intermediate, tod, end)

        # Access attributes
        print(transit_segment.start_wp)  # Output: Waypoint at (50.0, -0.5)
        print(
            transit_segment.intermediate_wps
        )  # Output: List of intermediate waypoints
        ```
    """

    start_wp: Waypoint
    toc_wp: Waypoint
    intermediate_wps: list[Waypoint]
    tod_wp: Waypoint
    end_wp: Waypoint

    def __init__(
        self,
        start_wp: Waypoint,
        toc_wp: Waypoint,
        intermediate_wps: list[Waypoint],
        tod_wp: Waypoint,
        end_wp: Waypoint,
    ) -> None:
        """Initializes an instance of the Transit class.

        This constructor sets up a transit segment by assigning the waypoints associated
        with the start, top-of-climb (TOC), intermediate waypoints, top-of-descent (TOD),
        and end points of the transit phase of a flight.

        Args:
            start_wp (Waypoint):
                The waypoint marking the beginning of the transit phase.
            toc_wp (Waypoint):
                The waypoint representing the top-of-climb (TOC) point.
            intermediate_wps (list[Waypoint]):
                A list of waypoints defining intermediate positions
                between the TOC and TOD waypoints.
            tod_wp (Waypoint):
                The waypoint representing the top-of-descent (TOD) point.
            end_wp (Waypoint):
                The waypoint marking the end of the transit phase.

        Example:
            ```python
            from my_module import Waypoint, Transit

            # Define waypoints
            start = Waypoint(lat=50.0, lon=-0.5)
            toc = Waypoint(lat=51.0, lon=-0.8)
            intermediate = [Waypoint(lat=51.5, lon=-1.0), Waypoint(lat=52.0, lon=-1.2)]
            tod = Waypoint(lat=52.5, lon=-1.4)
            end = Waypoint(lat=53.0, lon=-1.6)

            # Initialize a Transit object
            transit = Transit(start, toc, intermediate, tod, end)

            # Access attributes
            print(transit.start_wp)  # Output: Waypoint at (50.0, -0.5)
            print(transit.intermediate_wps)  # Output: List of Intermediate Waypoints
            ```
        """
        self.start_wp = start_wp
        self.toc_wp = toc_wp
        self.intermediate_wps = intermediate_wps
        self.tod_wp = tod_wp
        self.end_wp = end_wp


class TransitBuilder:
    """A builder class for constructing a transit route with waypoints and flight-level details.

    The `TransitBuilder` class facilitates the creation of a sequence of transit waypoints,
    including start, top-of-climb (TOC), intermediate waypoints, top-of-descent (TOD),
    and the ending waypoint for a given transit segment. It uses various performance data,
    transit segments, and flight configurations to compute accurate waypoint positions,
    altitudes, and timings.

    Attributes:
        transit_segments (list[Segment]):
            A list of `Segment` objects that define the transit portion of the route.
        transit_groundspeed_kts (int):
            The ground speed in knots for the transit segment.
        route_alt_ft (int):
            The altitude in feet for the route segment.
        departure_bearing_mag (int):
            The magnetic bearing for departure.
        flight_level (int):
            The calculated flight level for the transit. This is determined automatically
            during initialization.
        climb_performance_data (ClimbDescentPerformanceData | None):
            Performance data for the climb phase of the transit.
        descent_performance_data (ClimbDescentPerformanceData | None):
            Performance data for the descent phase of the transit.
        start_wp (Waypoint | None):
            The waypoint representing the start of the transit.
        toc_wp (Waypoint | None):
            The waypoint for the top-of-climb (TOC).
        intermediate_wps (list[Waypoint] | None):
            A list of intermediate waypoints in the transit.
        tod_wp (Waypoint | None):
            The waypoint for the top-of-descent (TOD).
        end_wp (Waypoint | None):
            The waypoint representing the end of the transit.

    Methods:
        __init__(self, transit_segments, transit_groundspeed_kts, route_alt_ft, departure_bearing_mag):
            Initializes a TransitBuilder with its key attributes.

        set_start(self) -> "TransitBuilder":
            Computes and assigns the start waypoint.

        set_toc(self) -> "TransitBuilder":
            Computes and assigns the top-of-climb (TOC) waypoint.

        set_intermediate_wps(self) -> "TransitBuilder":
            Computes and assigns the intermediate waypoints between TOC and TOD.

        set_tod(self) -> "TransitBuilder":
            Computes and assigns the top-of-descent (TOD) waypoint.

        set_end(self) -> "TransitBuilder":
            Computes and assigns the end waypoint for the transit segment.

        build(self) -> Transit:
            Constructs and returns a `Transit` object using the computed waypoints.

    Example:
        ```python
        # Define dummy transit segments and data
        segments = [
            Segment(
                start=Waypoint(lat=50, lon=0), end=Waypoint(lat=51, lon=1), length=100
            ),
            Segment(
                start=Waypoint(lat=51, lon=1), end=Waypoint(lat=52, lon=2), length=150
            ),
        ]

        builder = TransitBuilder(
            transit_segments=segments,
            transit_groundspeed_kts=400,
            route_alt_ft=5000,
            departure_bearing_mag=45,
        )

        # Configure the waypoints for each stage of the transit
        builder.set_start()
        builder.set_toc()
        builder.set_intermediate_wps()
        builder.set_tod()
        builder.set_end()

        # Build the Transit object
        transit = builder.build()
        print(transit.start_wp, transit.end_wp)
        ```
    """

    def __init__(
        self,
        transit_segments: list[Segment],
        transit_groundspeed_kts: int,
        route_alt_ft: int,
        departure_bearing_mag: int,
    ) -> None:
        """Initializes the TransitBuilder class with transit configuration and required attributes.

        This constructor sets up the TransitBuilder by providing the transit segments, ground speed,
        route altitude, and departure bearing. It initializes various attributes required for building
        the transit waypoints and computes the initial flight level using helper methods.

        Args:
            transit_segments (list[Segment]):
                A list of transit `Segment` objects that define the route segments for the transit phase.
            transit_groundspeed_kts (int):
                The ground speed in knots used to calculate transit timings and positions.
            route_alt_ft (int):
                The altitude for the route segment in feet used for waypoint calculations.
            departure_bearing_mag (int):
                The magnetic departure bearing, used to assign directional and waypoint identifiers.

        Attributes Initialized:
            transit_segments (list[Segment]): The transit route segments provided during initialization.
            transit_groundspeed_kts (int): The ground speed for the transit in knots.
            route_alt_ft (int): The transit route altitude in feet.
            departure_bearing_mag (int): The magnetic bearing for the departure route.
            flight_level (int): The estimated or computed flight level during transit, considered in hundreds of feet.
            climb_performance_data (ClimbDescentPerformanceData | None):
                Performance data for the transit climb phase, initialized based on flight level.
            descent_performance_data (ClimbDescentPerformanceData | None):
                Performance data for the transit descent phase, initialized based on flight level.
            start_wp (Waypoint | None): A `Waypoint` object representing the start of the transit phase.
            toc_wp (Waypoint | None): A `Waypoint` object representing the top-of-climb (TOC) point.
            intermediate_wps (list[Waypoint] | None): A list of `Waypoint` objects representing intermediate waypoints during transit.
            tod_wp (Waypoint | None): A `Waypoint` object representing the top-of-descent (TOD) point.
            end_wp (Waypoint | None): A `Waypoint` object representing the end of the transit phase.

        Notes:
            - This method calls the private `_set_flight_level_on_init` method to calculate the initial `flight_level`
              as well as set `climb_performance_data` and `descent_performance_data`.

        Example:
            ```python
            from my_module import Segment, TransitBuilder

            # Define dummy transit segments
            segments = [
                Segment(
                    start=Waypoint(lat=50, lon=0),
                    end=Waypoint(lat=51, lon=1),
                    length=100,
                ),
                Segment(
                    start=Waypoint(lat=51, lon=1),
                    end=Waypoint(lat=52, lon=2),
                    length=150,
                ),
            ]

            # Initialize the TransitBuilder
            builder = TransitBuilder(
                transit_segments=segments,
                transit_groundspeed_kts=400,
                route_alt_ft=5000,
                departure_bearing_mag=45,
            )

            print(builder.flight_level)  # Output: Computed flight level (e.g., 240)
            print(builder.transit_groundspeed_kts)  # Output: 400
            ```
        """
        self.transit_segments = transit_segments
        self.transit_groundspeed_kts = transit_groundspeed_kts
        self.route_alt_ft = route_alt_ft
        self.departure_bearing_mag = departure_bearing_mag
        self.flight_level: int
        self.climb_performance_data: ClimbDescentPerformanceData | None = None
        self.descent_performance_data: ClimbDescentPerformanceData | None = None
        self.start_wp: Waypoint | None = None
        self.toc_wp: Waypoint | None = None
        self.intermediate_wps: list[Waypoint] | None = None
        self.tod_wp: Waypoint | None = None
        self.end_wp: Waypoint | None = None

        self._set_flight_level_on_init()

    # -- Public methods -------------------------------------------------------

    def set_start(
        self,
    ) -> "TransitBuilder":
        """Start waypoint displays the departure bearing to the next waypoint."""
        departure_segment = self.transit_segments[0]
        departure_bearing = round(departure_segment.true_bearing)

        ident = f"0:00/{departure_bearing:03}"

        self.start_wp = deepcopy(departure_segment.start)
        self.start_wp.Type = "WAYPOINT"
        self.start_wp.Ident = ident
        self.start_wp.Comment = "START"

        return self

    def set_toc(self) -> "TransitBuilder":
        """Computes and assigns the Top-of-Climb (TOC) waypoint.

        This method calculates the position, identifier, and attributes for the
        TOC waypoint based on climb performance data and the first transit segment.
        The result is stored in the `toc_wp` attribute of the TransitBuilder instance.

        Raises:
            ValueError: If the flight level is not set before attempting to compute the TOC.

        Returns:
            TransitBuilder: The builder instance with the computed TOC waypoint added.

        Attributes Updated:
            toc_wp (Waypoint): The computed TOC waypoint with details like position, altitude, and identifier.

        Example:
            ```python
            builder = TransitBuilder(
                transit_segments=segments,
                transit_groundspeed_kts=400,
                route_alt_ft=5000,
                departure_bearing_mag=45,
            )

            # Ensure the flight level is set before calling set_toc
            builder.set_toc()

            print(builder.toc_wp)  # Output: Waypoint with TOC details
            ```
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
        """Computes and assigns intermediate waypoints for the transit route.

        This method calculates the intermediate waypoints based on the transit segments
        and their associated timing and positional data. It iterates over the route
        segments, determining the waypoint for each intermediate position while keeping
        track of cumulative time.

        The computed waypoints are stored in the `intermediate_wps` attribute of the
        TransitBuilder instance.

        Returns:
            TransitBuilder: The builder instance with the list of intermediate waypoints added.

        Attributes Updated:
            intermediate_wps (list[Waypoint]): A list of computed intermediate waypoints,
            deep-copied into the instance to prevent modifications to the original data.

        Notes:
            - The first segment is treated as containing the climb portion if it exists, and
              this impacts the calculation for that segment.
            - The cumulative time is updated with the travel time for each segment as waypoints are computed.

        Example:
            ```python
            builder = TransitBuilder(
                transit_segments=segments,
                transit_groundspeed_kts=400,
                route_alt_ft=5000,
                departure_bearing_mag=45,
            )

            # Compute the intermediate waypoints
            builder.set_intermediate_wps()

            # Access the list of intermediate waypoints
            print(builder.intermediate_wps)  # Output: List of intermediate Waypoints
            ```
        """
        # TODO Validate initial conditions

        intermediate_wps = []
        cum_time_secs = 0

        for idx, (this_segment, next_segment) in enumerate(
            zip(self.transit_segments, self.transit_segments[1:], strict=False),
        ):
            has_climb = idx == 0
            transit_wp, segment_time_secs = self._compute_intermediate_waypoint(
                has_climb=has_climb,
                this_segment=this_segment,
                next_segment=next_segment,
                cum_time_secs=cum_time_secs,
            )
            intermediate_wps.append(transit_wp)
            cum_time_secs += segment_time_secs

        self.intermediate_wps = deepcopy(intermediate_wps)

        return self

    def set_tod(self) -> "TransitBuilder":
        """Computes and assigns the Top-of-Descent (TOD) waypoint.

        This method calculates the TOD waypoint based on the total transit time,
        descent performance data, and the last segment of the transit route. The TOD
        waypoint includes the position, identifier, altitude, and associated timing details.

        The result is stored in the `tod_wp` attribute of the TransitBuilder instance.

        Raises:
            ValueError: If the flight level is not set before attempting to compute the TOD.

        Returns:
            TransitBuilder: The builder instance with the computed TOD waypoint added.

        Attributes Updated:
            tod_wp (Waypoint): The computed TOD waypoint, including position, identifier,
            and additional metadata.

        Notes:
            - This method relies on the `_compute_tod_time_secs` helper for calculating
              the time at which the descent begins.
            - The last segment of the transit route is used to determine the TOD position.

        Example:
            ```python
            builder = TransitBuilder(
                transit_segments=segments,
                transit_groundspeed_kts=400,
                route_alt_ft=5000,
                departure_bearing_mag=45,
            )

            # Ensure the flight level is set before calling set_tod
            builder.set_tod()

            print(builder.tod_wp)  # Output: Waypoint with TOD details
            ```
        """
        if self.flight_level is None:
            raise ValueError("Flight level must be set before setting TOD WP")

        tod_time_secs = self._compute_tod_time_secs()

        pos = self._compute_pos(
            self.descent_performance_data,
            self.transit_segments[-1],
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
        """Computes and assigns the End waypoint (LLEP) for the transit route.

        This method calculates the End waypoint (LLEP) based on the descent performance data,
        transit timing, and positional data from the last segment of the route. The waypoint
        is updated with appropriate altitude, identifier, and metadata.

        The resulting waypoint is stored in the `end_wp` attribute of the TransitBuilder instance.

        Raises:
            ValueError: If the descent performance data is not set before attempting to compute the End waypoint.

        Returns:
            TransitBuilder: The builder instance with the computed End waypoint added.

        Attributes Updated:
            end_wp (Waypoint): The computed End waypoint (LLEP) with updated position,
            identifier, and metadata such as altitude and comments.

        Notes:
            - The `tod_time_secs` and the descent time (from `descent_performance_data`) are used
              to calculate the total transit time used in the waypoint identifier.
            - The last segment's ending position is used as the base for the End waypoint.

        Example:
            ```python
            builder = TransitBuilder(
                transit_segments=segments,
                transit_groundspeed_kts=400,
                route_alt_ft=5000,
                departure_bearing_mag=45,
            )

            # Ensure descent performance data is set before calling set_end
            builder.set_end()

            print(builder.end_wp)  # Output: Waypoint with End (LLEP) details
            ```
        """
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
        """Constructs and returns a Transit object.

        This method creates and returns a fully constructed `Transit` object using
        the waypoints computed and stored in the builder instance. It uses the following
        waypoints: start, top-of-climb (TOC), intermediate, top-of-descent (TOD), and end.

        Returns:
            Transit: A Transit object containing all the relevant waypoints required to
            define the transit route.

        Waypoints Used:
            - `start_wp`: The starting waypoint of the transit route.
            - `toc_wp`: The Top-of-Climb waypoint, marking the climb completion.
            - `intermediate_wps`: A list of waypoints between TOC and TOD.
            - `tod_wp`: The Top-of-Descent waypoint, marking the beginning of descent.
            - `end_wp`: The ending waypoint of the transit route.

        Example:
            ```python
            builder = TransitBuilder(
                transit_segments=segments,
                transit_groundspeed_kts=400,
                route_alt_ft=5000,
                departure_bearing_mag=45,
            )

            # Build the transit after setting all the necessary waypoints
            builder.set_start()
            builder.set_toc()
            builder.set_intermediate_wps()
            builder.set_tod()
            builder.set_end()

            transit = builder.build()

            print(transit)  # Output: Transit object with all waypoints included
            ```
        """
        return Transit(
            start_wp=self.start_wp,
            toc_wp=self.toc_wp,
            intermediate_wps=self.intermediate_wps,
            tod_wp=self.tod_wp,
            end_wp=self.end_wp,
        )

    # -- Private methods --------------------------------------------------------

    def _set_flight_level_on_init(self) -> "TransitBuilder":
        """Initializes and sets the flight level (FL) for the transit route.

        This private method calculates an appropriate flight level for the transit route
        based on the total transit length and bearing. The flight level is adjusted to
        comply with eastbound or westbound flight level conventions. Additionally,
        the method retrieves and stores climb and descent performance data for the set
        flight level.

        Returns:
            TransitBuilder: The builder instance with the flight level and performance
            data initialized.

        Attributes Updated:
            flight_level (int): The calculated flight level (nearest multiple of 10).
            climb_performance_data (object): Performance data for normal climb at the
            calculated flight level.
            descent_performance_data (object): Performance data for descent at the
            calculated flight level.

        Notes:
            - The transit length is summed from all segments.
            - The bearing is computed to determine whether the flight is eastbound
              (0° to <180°) or westbound (180° to <360°):
                - Eastbound flights use odd flight levels.
                - Westbound flights use even flight levels.
            - The flight level is computed from twice the transit length, ensuring it
              adheres to the required odd/even convention using bitwise operations.

        Example:
            ```python
            builder = TransitBuilder(transit_segments=segments)

            # Initialize the flight level and performance data
            builder._set_flight_level_on_init()

            print(builder.flight_level)  # Output: Flight level set based on transit
            print(builder.climb_performance_data)  # Output: Climb performance data
            print(builder.descent_performance_data)  # Output: Descent performance data
            ```
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
            JetOperation.NORMAL_CLIMB,
            self.flight_level,
        )
        self.descent_performance_data = get_climb_descent_performance_data(
            JetOperation.NAV_DESCENT,
            self.flight_level,
        )

    def _compute_tod_time_secs(self) -> float:
        """Computes the Top-of-Descent (TOD) time in seconds.

        This private method calculates the time at which the top-of-descent should occur,
        based on transit distance, climb and descent performance data, and the transit
        groundspeed. The TOD time represents the cumulative time (in seconds) from the
        start of the transit until the point where descent should begin.

        Returns:
            float: The computed TOD time in seconds.

        Raises:
            ValueError: If the `climb_performance_data` is not set.
            ValueError: If the `descent_performance_data` is not set.

            Both conditions require that the flight level (FL) be set before calling
            this method.

        Calculation Details:
            1. Subtracts the climb and descent distances (in nautical miles) from the
               total transit distance to calculate the cruise distance.
            2. Calculates the transit time for this cruise distance using:
               - `transit_groundspeed_kts` (transit groundspeed in knots).
               - Formula: `transit_time_secs = (3600 * transit_distance_nm) / groundspeed`.
            3. Combines the climb time and cruise time to determine the cumulative TOD time.

        Notes:
            - The method assumes that the flight level and its associated performance
              data for both climb and descent are already initialized.

        Example:
            ```python
            builder = TransitBuilder(
                transit_segments=segments,
                transit_groundspeed_kts=400,
            )

            builder._set_flight_level_on_init()
            tod_time_secs = builder._compute_tod_time_secs()

            print(tod_time_secs)  # Output: TOD time in seconds
            ```
        """
        if self.climb_performance_data is None:
            raise ValueError("FL must be set before setting END WP")
        if self.descent_performance_data is None:
            raise ValueError("FL must be set before setting END WP")

        transit_distance_nm = self._compute_transit_distance_nm() - (
            self.climb_performance_data.distance_nm
            + self.descent_performance_data.distance_nm
        )
        transit_time_secs = 3600 * transit_distance_nm / self.transit_groundspeed_kts

        return self.climb_performance_data.time_secs + transit_time_secs

    def _compute_pos(
        self,
        performance_data: ClimbDescentPerformanceData,
        segment: Segment,
    ) -> Pos:
        """Computes the position of a waypoint within a segment using performance data.

        This private method calculates the position (`Pos`) of a waypoint, such as
        Top-of-Climb (TOC) or Top-of-Descent (TOD), based on the specified performance
        data and the segment's geometry. It uses the performance data to determine how
        far along the segment the waypoint is located and interpolates its latitude,
        longitude, and altitude accordingly.

        Args:
            performance_data (object): An object containing performance details, including
            the distance traveled (in nautical miles) required to reach the waypoint.
            segment (Segment): The segment along which the position is being computed.

        Returns:
            Pos: A position object containing interpolated latitude, longitude, and
            altitude values. The altitude is set to the flight level (FL) multiplied by 100.

        Raises:
            ValueError: If the flight level (`flight_level`) is not set prior to calling
            this method.

        Calculation Details:
            1. Computes the fraction of the segment covered by the waypoint using:
               - `percent_of_leg = 1.0 - (performance_data.distance_nm / segment.length)`.
            2. Uses the `interpolate_lat_lon_flat` function to find the latitude and
               longitude at the interpolated position along the segment.
            3. Sets the altitude (`@Alt`) to the flight level (`flight_level`) multiplied
               by 100, as it represents altitude in feet.

        Notes:
            - The flight level (`flight_level`) must already be initialized before calling
              this method.
            - This method assumes a flat-earth interpolation model using
              `interpolate_lat_lon_flat`.

        Example:
            ```python
            builder = TransitBuilder(transit_segments=segments)

            builder._set_flight_level_on_init()
            pos = builder._compute_pos(
                performance_data=builder.climb_performance_data,
                segment=segments[0],
            )

            print(
                pos
            )  # Output: Pos object with interpolated latitude, longitude, and altitude
            ```
        """
        if self.flight_level is None:
            raise ValueError("FL must be set before setting END WP")

        percent_of_leg = 1.0 - performance_data.distance_nm / segment.length
        lat, lon = interpolate_lat_lon_flat(segment, percent_of_leg)
        alt = int(self.flight_level * 100.0)

        return Pos(**{"@Lon": lon, "@Lat": lat, "@Alt": alt})

    def _compute_transit_distance_nm(self) -> float:
        """Computes the total transit distance in nautical miles (NM).

        This private method calculates the sum of the lengths of all segments in the
        transit route to determine the total transit distance. Each segment's length
        is assumed to be provided in nautical miles.

        Returns:
            float: The total transit distance in nautical miles.

        Calculation Details:
            - Iterates over the segments in `self.transit_segments`.
            - Sums up the `length` attribute of each segment to compute the total distance.

        Example:
            ```python
            builder = TransitBuilder(transit_segments=segments)
            total_distance_nm = builder._compute_transit_distance_nm()

            print(total_distance_nm)  # Output: Total transit distance in nautical miles
            ```
        """
        return sum(segment.length for segment in self.transit_segments)

    def _compute_intermediate_waypoint(
        self,
        *,
        has_climb: bool,
        this_segment: Segment,
        next_segment: Segment,
        cum_time_secs: int,
    ) -> tuple[Waypoint, int]:
        """Computes an intermediate waypoint and its associated travel time for a given segment.

        This private method calculates an intermediate waypoint's position, identifier,
        and other attributes based on the traversed segment and the cumulative travel time.
        The method accounts for whether the segment includes a climb phase, and adjusts
        the flight time and waypoint attributes accordingly.

        Args:
            has_climb (bool): Indicates whether the segment includes a climb phase.
            this_segment (Segment): The current segment from which the intermediate waypoint
                is computed.
            next_segment (Segment): The next segment in the route, used to determine
                departure bearing.
            cum_time_secs (int): The cumulative travel time (in seconds) prior to this segment.

        Returns:
            tuple[Waypoint, int]: A tuple containing:
                - `Waypoint`: The computed intermediate waypoint, including position (`Pos`),
                  type, identifier, and altitude.
                - `int`: The total segment travel time (in seconds), including climb time if
                  applicable.

        Calculation Details:
            - If `has_climb` is `True`:
                - Calculates the cruise distance by subtracting the climb distance
                  (`climb_performance_data.distance_nm`) from the segment's total length.
                - Computes the cruise time based on transit groundspeed (`transit_groundspeed_kts`).
                - Adds the climb time (`climb_performance_data.time_secs`) to the cruise time.
            - If `has_climb` is `False`:
                - Directly determines the segment travel time using the segment's length and
                  transit groundspeed.
            - The waypoint's identifier (`wp.Ident`) is constructed in the format:
              `"<cumulative time in mins:secs>/<departure bearing>/<optional comment>"`.
            - The altitude (`wp.Pos.Alt`) is set to the flight level (`flight_level`) multiplied by 100.

        Attributes Updated on `Waypoint`:
            - `Type`: Set to `"WAYPOINT"`.
            - `Ident`: Populated with the formatted identifier.
            - `Pos.Alt`: Altitude in feet, calculated as `flight_level * 100`.

        Raises:
            ValueError: If `flight_level` is not set before calling this method.

        Notes:
            - The method uses `self.transit_groundspeed_kts` to compute travel times.
            - The `deepcopy` of the segment's end position ensures no mutation to the original object.

        Example:
            ```python
            builder = TransitBuilder(transit_segments=segments)
            builder._set_flight_level_on_init()

            wp, segment_time = builder._compute_intermediate_waypoint(
                has_climb=True,
                this_segment=current_segment,
                next_segment=next_segment,
                cum_time_secs=1000,
            )

            print(wp.Type)  # Output: WAYPOINT
            print(wp.Ident)  # Output: "<cumulative time>/<bearing>/<optional comment>"
            print(segment_time)  # Output: Travel time for the segment in seconds
            ```
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
                this_segment.travel_time_secs(self.transit_groundspeed_kts),
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


def _compute_transit_segments(route: list[Waypoint], id_entry: int) -> list[Segment]:
    """Computes the transit segments for a route based on a specified entry waypoint index.

    This private method creates a list of `Segment` objects that represent the portions
    of a route from the start of the route up to (but not including) the waypoint at the
    specified `id_entry`. Each segment is constructed from consecutive waypoints along
    the route.

    Args:
        route (list[Waypoint]): A list of waypoints that define the overall route.
        id_entry (int): The 1-based index of the entry waypoint. Only segments up to
            this waypoint are included in the returned list.

    Returns:
        list[Segment]: A list of `Segment` objects, where each segment is defined
        by a pair of consecutive waypoints from the input route.

    Raises:
        ValueError: If `id_entry` is less than 1 or greater than the number of waypoints
        in the route. The `id_entry` index must be valid for the input `route`.

    Calculation Details:
        - Converts the 1-based `id_entry` index to a 0-based index (`idx_entry`).
        - Iterates over the waypoints in the route up to the waypoint at `idx_entry`.
        - For each pair of consecutive waypoints, creates a `Segment` object using deep
          copies of the waypoints to avoid unintended modifications.

    Notes:
        - The method ensures that created `Segment` objects are independent of the
          original `route` by making deep copies of each waypoint.
        - Segments will not include the waypoint at `id_entry` or any subsequent
          waypoints.

    Example:
        ```python
        route = [
            Waypoint(id=1, lat=10.0, lon=20.0, alt=30000),
            Waypoint(id=2, lat=15.0, lon=25.0, alt=30000),
            Waypoint(id=3, lat=20.0, lon=30.0, alt=30000),
        ]
        id_entry = 3

        builder = TransitBuilder()
        segments = builder._compute_transit_segments(route, id_entry)

        for segment in segments:
            print(segment.start, segment.end)
        # Output: Prints the start and end waypoints of the segments.
        ```
    """
    idx_entry = id_entry - 1

    if idx_entry < 0 or idx_entry >= len(route):
        raise ValueError("entry id must be between 0 and the number of waypoints")

    segments = []
    for i in range(0, idx_entry):
        segments.append(Segment(deepcopy(route[i]), deepcopy(route[i + 1])))

    return segments


def _compute_transit_fl(transit_segments: list[Segment]) -> int:
    """Computes the flight level (FL) for transit based on the total route length and bearing.

    This private method calculates a suggested flight level (FL) for a set of transit segments.
    The resulting FL is adjusted to be odd or even based on the overall bearing of the route,
    following standard flight level rules (eastbound = odd, westbound = even). The flight level
    is also rounded to the nearest multiple of 10.

    Args:
        transit_segments (list[Segment]): A list of `Segment` objects representing the
        transit route.

    Returns:
        int: The computed flight level (FL), rounded and adjusted to the appropriate
        odd/even value based on bearing.

    Calculation Details:
        - Summarizes the total length of all transit segments to determine the overall route length (`transit_length`).
        - Calculates the route's overall bearing using `_compute_transit_bearing(transit_segments)`.
        - Computes the initial flight level (`transit_fl`) based on twice the `transit_length`.
        - Adjusts the flight level to ensure appropriate odd/even compliance based on the bearing:
            - Eastbound (0° ≤ bearing < 180°): FL must be odd.
            - Westbound (180° ≤ bearing < 360°): FL must be even.
        - Converts the result into an actual flight level by rounding it to the nearest multiple of 10.

    Notes:
        - Even and odd flight levels are used for compliance with standard flight rules for IFR operations:
          - Eastbound (0° ≤ bearing < 180°): Odd flight levels.
          - Westbound (180° ≤ bearing < 360°): Even flight levels.
        - The function ensures immutability of the input route, performing no modification on the segments.

    Example:
        ```python
        transit_segments = [
            Segment(
                start=Waypoint(lat=40.0, lon=-75.0),
                end=Waypoint(lat=41.5, lon=-72.5),
                length=120,
            ),
            Segment(
                start=Waypoint(lat=41.5, lon=-72.5),
                end=Waypoint(lat=43.0, lon=-70.0),
                length=135,
            ),
        ]

        builder = TransitBuilder()
        transit_fl = builder._compute_transit_fl(transit_segments)
        print(transit_fl)  # Output: A flight level value, e.g., 260
        ```
    """
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

    return (transit_fl // 10) * 10


def _compute_transit_bearing(transit_segments: list[Segment]) -> int:
    """Computes the overall transit bearing for a set of segments.

    This private method calculates the average or resultant bearing for a collection
    of transit segments by considering their individual bearings. The calculation
    combines the bearings into a single directional value using vector components.

    Args:
        transit_segments (list[Segment]): A list of `Segment` objects representing
        the transit route. Each `Segment` should have a `true_bearing` attribute.

    Returns:
        int: The overall bearing in degrees, as an integer between [0, 360).

    Calculation Details:
        - For each segment, the `true_bearing` attribute (provided in degrees)
          is converted to its corresponding unit vector components:
            - X component: `cos(true_bearing in radians)`
            - Y component: `sin(true_bearing in radians)`
        - Sums up all X and Y components across the transit segments.
        - Computes the arctangent of the resultant vector's components using
          `atan2(y, x)`, which provides the overall directional angle in radians.
        - Converts radians to degrees and ensures the result is in the range [0, 360)
          using the modulo operator.

    Notes:
        - The overall bearing represents the composite direction of transit segments
          treated as vectors.
        - The method assumes that the `true_bearing` attribute of each `Segment` is
          set and valid.

    Example:
        ```python
        transit_segments = [
            Segment(true_bearing=45),  # Segment with a bearing of 45°
            Segment(true_bearing=135),  # Segment with a bearing of 135°
            Segment(true_bearing=90),  # Segment with a bearing of 90°
        ]

        builder = TransitBuilder()
        overall_bearing = builder._compute_transit_bearing(transit_segments)
        print(overall_bearing)  # Output: Composite bearing as an integer in degrees
        ```
    """
    x = sum(
        math.cos(math.radians(segment.true_bearing)) for segment in transit_segments
    )
    y = sum(
        math.sin(math.radians(segment.true_bearing)) for segment in transit_segments
    )

    return int(math.degrees(math.atan2(y, x)) % 360)
