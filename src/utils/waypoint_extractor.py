"""
This script parses the test LNM plan file and extracts way points in a format
useful for a conftest.py route fixture.
"""

from conftest import data_path
from src.deserialisers.little_navmap import LittleNavmap


def process():
    file_path = data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    plan = LittleNavmap.read(file_path)
    # print(plan.Flightplan.Waypoints)

    print(
        ",\n".join(
            f"""Waypoint(
        Name={repr(waypoint.Name)},
        Ident={repr(waypoint.Ident)},
        Type={repr(waypoint.Type)},
        Region={repr(waypoint.Region)},
        Comment={repr(waypoint.Comment)},
        Pos=Pos(**{{
            "@Lon": {waypoint.Pos.Lon},
            "@Lat": {waypoint.Pos.Lat},
            "@Alt": {waypoint.Pos.Alt}
        }}),
    )"""
            for waypoint in plan.Flightplan.Waypoints
        )
    )


if __name__ == "__main__":
    process()
