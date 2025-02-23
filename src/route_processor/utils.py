"""Utility functions for route and waypoint processing.

Functions:
- interpolate_lat_lon_flat: Calculate the latitude and longitude of a point along a flat-Earth segment.
- mins_secs_str: Convert time in seconds to a minutes:seconds string format.
- compute_departure_bearing: Calculate the departure bearing for a given waypoint.
"""

from src.deserialisers.little_navmap import Waypoint
from src.route_processor.geo import Segment


def interpolate_lat_lon_flat(segment: Segment, percent):
    """Interpolates a latitude and longitude along a segment using linear interpolation.

    This function computes an interpolated position (latitude and longitude) a certain
    percentage along a given segment. The interpolation assumes a flat Earth model,
    which is appropriate for small distances or where extreme precision is not required.

    Args:
        segment (Segment): The segment along which the interpolation is computed.
            The segment must include `start` and `end` points, each with `Lat` and `Lon`
            attributes representing their latitude and longitude, respectively.
        percent (float): A fractional value between 0.0 and 1.0 (inclusive) that
            specifies the proportion of the distance along the segment at which
            the interpolation is calculated:
            - `0.0`: Returns the start point of the segment.
            - `1.0`: Returns the end point of the segment.
            - Intermediate values return a position proportionally between the
              start and end points.

    Returns:
        tuple[float, float]: A tuple containing:
            - `lat` (float): The interpolated latitude.
            - `lon` (float): The interpolated longitude.

    Raises:
        ValueError: If `percent` is not between 0.0 and 1.0 (inclusive).

    Calculation Details:
        - Uses linear interpolation for both latitude and longitude:
            - `lat = lat1 + percent * (lat2 - lat1)`
            - `lon = lon1 + percent * (lon2 - lon1)`
        - This calculation assumes the Earth is flat, disregarding curvature.

    Notes:
        - As the function assumes a flat Earth, results may contain minor inaccuracies
          for segments spanning large distances or near the poles.
        - The function relies on the `Lat` and `Lon` attributes being present in the
          `start` and `end` points of the segment.

    Example:
        ```python
        segment = Segment(
            start=Waypoint(Pos=Position(Lat=40.0, Lon=-75.0)),
            end=Waypoint(Pos=Position(Lat=41.0, Lon=-74.0)),
        )

        # Interpolate halfway along the segment
        lat, lon = interpolate_lat_lon_flat(segment, percent=0.5)
        print(lat, lon)  # Output: 40.5, -74.5

        # At the start of the segment
        lat, lon = interpolate_lat_lon_flat(segment, percent=0.0)
        print(lat, lon)  # Output: 40.0, -75.0

        # At the end of the segment
        lat, lon = interpolate_lat_lon_flat(segment, percent=1.0)
        print(lat, lon)  # Output: 41.0, -74.0
        ```
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


def mins_secs_str(time_in_seconds) -> str:
    """Converts a time duration from seconds into a string formatted as minutes and seconds.

    This function takes a time value in seconds and converts it into a string in the
    format `MM:SS`, where `MM` is the number of minutes and `SS` is the number of seconds
    (always displayed as two digits).

    Args:
        time_in_seconds (float or int): The time duration in seconds to be converted.
        It can be an integer or a float. Fractional seconds will be truncated.

    Returns:
        str: A string representing the time in the format `MM:SS`, where:
            - `MM` is the integer number of minutes.
            - `SS` is the integer number of seconds, zero-padded to two digits.

    Calculation Details:
        - Minutes are calculated by performing integer division of the input by 60.
        - Seconds are calculated by taking the remainder of the total seconds when
          divided by 60 (`time_in_seconds % 60`).
        - The result is formatted as `MM:SS` using Python's string formatting,
          ensuring seconds are displayed as two digits.

    Notes:
        - The function does not handle negative time values; ensure that the input
          is non-negative before calling the function.
        - Fractional seconds are discarded, as only whole minutes and seconds are represented.

    Example:
        ```python
        # Convert 125 seconds to MM:SS format
        formatted_time = mins_secs_str(125)
        print(formatted_time)  # Output: "2:05"

        # Convert exactly 60 seconds
        formatted_time = mins_secs_str(60)
        print(formatted_time)  # Output: "1:00"

        # Convert less than a full minute
        formatted_time = mins_secs_str(45)
        print(formatted_time)  # Output: "0:45"

        # Convert a float duration (truncates fractional part)
        formatted_time = mins_secs_str(123.987)
        print(formatted_time)  # Output: "2:03"
        ```
    """
    mins = int(time_in_seconds / 60)
    secs = int(time_in_seconds % 60)

    return f"{mins}:{secs:02}"


def compute_departure_bearing(route: list[Waypoint], wp_id: int) -> int:
    """Computes the departure bearing from a specific waypoint in a route.

    This function calculates the true bearing of the segment (direction)
    between a waypoint specified by its index in the route and the next waypoint.

    Args:
        route (list[Waypoint]): A list of `Waypoint` objects that make up the route.
            Each `Waypoint` must have sufficient data to be used in a `Segment` for
            bearing computation.
        wp_id (int): The index of the starting waypoint in the route. The function
            calculates the bearing using the waypoint at `wp_id` as the starting point
            and the waypoint at `wp_id + 1` as the ending point.

    Returns:
        int: The computed true bearing in degrees, rounded to the nearest integer.

    Calculation Details:
        - Extracts the starting waypoint (`start_wp`) using `wp_id` and the next
          waypoint (`end_wp`) using `wp_id + 1` from the route.
        - Creates a `Segment` from `start_wp` to `end_wp`.
        - Computes true bearing from the segment and rounds it to the nearest integer.

    Raises:
        IndexError: If `wp_id + 1` is out of bounds for the `route` list, i.e., there
        are no subsequent waypoints to calculate a bearing.

    Notes:
        - The function assumes the provided `route` has a valid sequence of waypoints.
        - The bearing is calculated for the segment between `wp_id` and `wp_id + 1`.

    Example:
        ```python
        # Define a list of waypoints
        route = [
            Waypoint(Pos=Position(Lat=40.0, Lon=-75.0)),
            Waypoint(Pos=Position(Lat=41.0, Lon=-74.0)),
            Waypoint(Pos=Position(Lat=42.0, Lon=-73.0)),
        ]

        # Compute the departure bearing from the first waypoint
        dep_bearing = compute_departure_bearing(route, wp_id=0)
        print(dep_bearing)  # Output: Bearing in degrees between waypoints 0 and 1

        # Compute the departure bearing from the second waypoint
        dep_bearing = compute_departure_bearing(route, wp_id=1)
        print(dep_bearing)  # Output: Bearing in degrees between waypoints 1 and 2
        ```
    """
    start_wp = route[wp_id]
    end_wp = route[wp_id + 1]
    departure_segment = Segment(start_wp, end_wp)

    return round(departure_segment.true_bearing)
