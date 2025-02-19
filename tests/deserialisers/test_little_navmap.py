from conftest import test_data_path
from deserialisers.little_navmap import Flightplan


def test_little_navmap_read():
    file_path = test_data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"

    plan = Flightplan.read(file_path)

    assert plan.Header.CreationDate == "2025-02-18T16:37:34+00:00"
    assert plan.Waypoints[0].Ident == "EGNT"


def test_little_navmap_write():
    file_path = test_data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    plan = Flightplan.read(file_path)

    outfile = test_data_path() / "outfile.lnmpln"
    plan.write(outfile)

    assert True
