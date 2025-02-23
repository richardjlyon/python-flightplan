import pytest

from src.deserialisers.little_navmap import Waypoint, Pos
from src.route_processor.geo import Segment
from src.route_processor.route_processor import process_route, ProcessorConfig

montrose = Waypoint(
    Name="Montrose",
    Ident="LLEP",
    Type="USER",
    Region=None,
    Comment=None,
    Pos=Pos(**{"@Lon": -2.475614, "@Lat": 56.70507, "@Alt": 22000.0}),
)

forfar = Waypoint(
    Name="Forfar",
    Ident="WP1",
    Type="USER",
    Region=None,
    Comment=None,
    Pos=Pos(**{"@Lon": -2.92245, "@Lat": 56.632725, "@Alt": 22000.0}),
)


@pytest.fixture
def montrose_to_forfar():
    """Fixture for a segment representing a route from Edinburgh to Glasgow."""
    return Segment(montrose, forfar)


@pytest.fixture
def route():
    """Fixture for a route."""
    return [
        Waypoint(
            Name="Newcastle",
            Ident="EGNT",
            Type="AIRPORT",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -1.689722, "@Lat": 55.038055, "@Alt": 266}),
        ),
        Waypoint(
            Name="Saint Abbs",
            Ident="SAB",
            Type="VOR",
            Region="EG",
            Comment="112.5",
            Pos=Pos(**{"@Lon": -2.206336, "@Lat": 55.907513, "@Alt": 14480}),
        ),
        Waypoint(
            Name="Montrose",
            Ident="LLEP",
            Type="USER",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -2.475614, "@Lat": 56.70507, "@Alt": 22000}),
        ),
        Waypoint(
            Name="Forfar",
            Ident="WP1",
            Type="USER",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -2.92245, "@Lat": 56.632725, "@Alt": 22000}),
        ),
        Waypoint(
            Name="Crathie",
            Ident="WP2",
            Type="USER",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -3.215497, "@Lat": 57.040005, "@Alt": 22000}),
        ),
        Waypoint(
            Name="Braemar",
            Ident="WP3",
            Type="USER",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -3.483008, "@Lat": 56.991013, "@Alt": 22000}),
        ),
        Waypoint(
            Name="Tummel",
            Ident="WP4",
            Type="USER",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -4.012328, "@Lat": 56.70752, "@Alt": 21005}),
        ),
        Waypoint(
            Name="Rannoch",
            Ident="WP5",
            Type="USER",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -4.43118, "@Lat": 56.684898, "@Alt": 17440}),
        ),
        Waypoint(
            Name="Loch Ericht",
            Ident="WP6",
            Type="USER",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -4.466886, "@Lat": 56.747452, "@Alt": 16428}),
        ),
        Waypoint(
            Name="Dalwhinnie",
            Ident="WP7",
            Type="USER",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -4.247161, "@Lat": 56.93224, "@Alt": 13027}),
        ),
        Waypoint(
            Name="Fort Augustus",
            Ident="WP8",
            Type="USER",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -4.67408, "@Lat": 57.136242, "@Alt": 8258}),
        ),
        Waypoint(
            Name=None,
            Ident="CI05",
            Type="WAYPOINT",
            Region="EG",
            Comment="ILS108.5/RW05",
            Pos=Pos(**{"@Lon": -4.328055, "@Lat": 57.41526, "@Alt": 3075}),
        ),
        Waypoint(
            Name="Inverness",
            Ident="EGPE",
            Type="AIRPORT",
            Region=None,
            Comment=None,
            Pos=Pos(**{"@Lon": -4.0475, "@Lat": 57.5425, "@Alt": 31}),
        ),
    ]


@pytest.fixture
def config():
    """Fixture for a route processor config."""
    return ProcessorConfig(
        id_entry=3, id_exit=12, route_airspeed_kts=420, transit_airspeed_kts=495
    )


@pytest.fixture
def processed_route(route, config):
    """Fixture for a processed route."""
    return process_route(route, config)
