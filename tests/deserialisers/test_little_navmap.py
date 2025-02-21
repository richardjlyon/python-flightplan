from conftest import data_path
from src.deserialisers.little_navmap import LittleNavmap


def test_littlenavmap_read():
    file_path = data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    plan = LittleNavmap.read(file_path)

    assert plan.Flightplan.Header.FlightplanType == "VFR"
