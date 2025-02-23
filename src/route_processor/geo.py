"""This module provides functionalities for geographical computations and analysis.

Features:
- Represents segments between waypoints with attributes such as starting and ending positions.
- Calculates distances, true bearings, and magnetic bearings between waypoints.
- Integrates with pygeomag to account for Earth's magnetic declination.
- Offers computations for travel times based on speed and other utilities.

Dependencies:
- pygeomag: For magnetic declination calculations.
- Waypoint class: Represents positions involved in calculations.
"""

import math
from pygeomag import GeoMag

from src.deserialisers.little_navmap import Waypoint

geo_mag = GeoMag()


class Segment:
    """Represents a segment connecting two waypoints.

    Attributes:
        start (Waypoint): The starting waypoint of the segment.
        end (Waypoint): The ending waypoint of the segment.
    """

    start: Waypoint
    end: Waypoint

    def __init__(self, start: Waypoint, end: Waypoint):
        """Initializes a segment with the provided start and end waypoints.

        Args:
            start (Waypoint): The starting waypoint of the segment.
            end (Waypoint): The ending waypoint of the segment.
        """
        self.start = start
        self.end = end

    def __repr__(self):
        """Returns a string representation of the segment, including its start, end, and length.

        Returns:
            str: The string representation of the segment.
        """
        return f"Segment(start={self.start}, end={self.end}, length={self.length:.2f})"

    @property
    def length(self) -> float:
        """Computes the flat earth distance between the start and end waypoints.

        The calculation assumes a spherical Earth and uses an approximation of
        the Haversine formula for flat distances over short arcs.

        Returns:
            float: The distance in nautical miles.
        """
        R = 3440.065  # Earth's radius in nautical miles
        lat1, lon1, lat2, lon2 = map(
            math.radians,
            [
                self.start.Pos.Lat,
                self.start.Pos.Lon,
                self.end.Pos.Lat,
                self.end.Pos.Lon,
            ],
        )

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        x = dlon * math.cos((lat1 + lat2) / 2)
        distance = R * math.sqrt(x * x + dlat * dlat)

        return distance

    @property
    def true_bearing(self) -> int:
        """Calculates the true bearing between the start and end waypoints.

        True bearing is the compass direction from the start waypoint to the
        end waypoint relative to true north.

        Returns:
            int: The true bearing in degrees (0-359).
        """
        lat1, lon1, lat2, lon2 = map(
            math.radians,
            [
                self.start.Pos.Lat,
                self.start.Pos.Lon,
                self.end.Pos.Lat,
                self.end.Pos.Lon,
            ],
        )

        dlon = lon2 - lon1

        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(
            lat2
        ) * math.cos(dlon)

        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360

        return round(bearing % 360)

    @property
    def magnetic_bearing(self) -> int:
        """Calculates the magnetic bearing between start and end waypoints.

        The magnetic bearing takes into account the magnetic declination at the
        midpoint of the segment.

        Returns:
            int: The magnetic bearing in degrees (0-359).
        """
        avg_lat = (self.start.Pos.Lat + self.end.Pos.Lat) / 2
        avg_lon = (self.start.Pos.Lon + self.end.Pos.Lon) / 2
        declination = get_magnetic_declination(avg_lat, avg_lon)

        return round((self.true_bearing + declination) % 360)

    def travel_time_secs(self, speed_kts: float) -> float:
        """Calculates the travel time along the segment at a given speed.

        Args:
            speed_kts (float): The speed in knots.

        Returns:
            float: The travel time in seconds.
        """
        return (self.length / speed_kts) * 3600


def get_magnetic_declination(lat, lon):
    """Calculates the magnetic declination for a given geographic location.

    Magnetic declination is the angle between geographic north and magnetic north at a specific
    location on the Earth's surface.

    Args:
        lat (float): The latitude of the location in decimal degrees.
                     Positive for north and negative for south.
        lon (float): The longitude of the location in decimal degrees.
                     Positive for east and negative for west.

    Returns:
        float: The magnetic declination at the specified location in degrees.
               Positive values indicate eastward declination, and negative values indicate
               westward declination.

    Notes:
        - The altitude is set to sea level (0 kilometers).
        - The calculation uses the date 2025.13 in decimal years (February 19, 2025).
        - The declination is calculated using the `geo_mag.calculate` method.
    """
    alt = 0  # Altitude in kilometers, set to 0 for sea level
    time = 2025.13  # Current date in decimal years (February 19, 2025)
    result = geo_mag.calculate(lat, lon, alt, time)
    return result.d  # declination in degrees
