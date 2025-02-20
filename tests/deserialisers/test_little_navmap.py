from conftest import data_path
from deserialisers.little_navmap import Flightplan


def test_little_navmap_read():
    file_path = data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"

    plan = Flightplan.read(file_path)

    assert plan.Header.CreationDate == "2025-02-19T22:22:28+00:00"
    assert len(plan.Waypoints) == 13
    assert plan.Waypoints[0].Ident == "EGNT"


def test_little_navmap_write():
    file_path = data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    plan = Flightplan.read(file_path)

    outfile = data_path() / "outfile.lnmpln"
    plan.write(outfile)

    assert True
