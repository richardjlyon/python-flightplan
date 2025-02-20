from conftest import data_path
from deserialisers.little_navmap import LittleNavmap


def test_littlenavmap_read():
    file_path = data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    plan = LittleNavmap.read(file_path)

    assert plan.Flightplan.Header.FlightplanType == "VFR"


def test_littlenavmap_write():
    file_path = data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    plan = LittleNavmap.read(file_path)

    outfile = data_path() / "outfile_2.lnmpln"
    plan.write(outfile)

    assert True
