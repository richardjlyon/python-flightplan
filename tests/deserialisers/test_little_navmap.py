"""Tests Little Navmap deserialiser functionality."""

from conftest import data_path
from src.deserialisers.little_navmap import LittleNavmap


def test_littlenavmap_read():
    """Tests the ability of `LittleNavmap.read` to correctly parse a `.lnmpln` flight plan file.

    This function validates that the `LittleNavmap.read` method successfully reads and
    deserializes a flight plan file into a Python object, and verifies a specific property
    in the result to ensure the data is correctly parsed.
    """
    file_path = data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    plan = LittleNavmap.read(file_path)

    assert plan.Flightplan.Header.FlightplanType == "VFR"
