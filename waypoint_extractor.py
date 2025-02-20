"""
This script parses the test LNM plan file and extracts way points in a format
useful for a conftest.py route fixture.
"""

from conftest import data_path
from deserialisers.little_navmap import Flightplan


def process():
    file_path = data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    plan = Flightplan.read(file_path)

    print(",\n".join(repr(waypoint) for waypoint in plan.Waypoints))


if __name__ == "__main__":
    process()
