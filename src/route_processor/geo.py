import math
from pygeomag import GeoMag

from src.deserialisers.little_navmap import Waypoint

geo_mag = GeoMag()


class Segment:
    start: Waypoint
    end: Waypoint

    def __init__(self, start: Waypoint, end: Waypoint):
        self.start = start
        self.end = end

    def __repr__(self):
        return f"Segment(start={self.start}, end={self.end}, length={self.length:.2f})"

    @property
    def length(self) -> float:
        """Compute the flat earth distance between start and end."""

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
        avg_lat = (self.start.Pos.Lat + self.end.Pos.Lat) / 2
        avg_lon = (self.start.Pos.Lon + self.end.Pos.Lon) / 2
        declination = get_magnetic_declination(avg_lat, avg_lon)

        return round((self.true_bearing + declination) % 360)

    def travel_time_secs(self, speed_kts: float) -> float:
        return (self.length / speed_kts) * 3600


def get_magnetic_declination(lat, lon):
    alt = 0  # Altitude in kilometers, set to 0 for sea level
    time = 2025.13  # Current date in decimal years (February 19, 2025)
    result = geo_mag.calculate(lat, lon, alt, time)
    return result.d  # declination in degrees
