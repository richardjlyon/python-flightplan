from typing import List

from src.deserialisers.little_navmap import Waypoint
from src.route_processor.geo import Segment


def interpolate_lat_lon_flat(segment: Segment, percent):
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


def mins_secs_str(time_in_seconds) -> str:
    """Return mins and seconds as a string from seconds."""
    mins = int(time_in_seconds / 60)
    secs = int(time_in_seconds % 60)

    return f"{mins}:{secs:02}"


def compute_departure_bearing(route: List[Waypoint], wp_id: int) -> int:
    """Compute the departure bearing of waypoint wp_id."""
    start_wp = route[wp_id]
    end_wp = route[wp_id + 1]
    departure_segment = Segment(start_wp, end_wp)

    return round(departure_segment.true_bearing)
