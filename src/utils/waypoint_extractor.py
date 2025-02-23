"""A utility for dumping waypoints in a plan for testing."""

from conftest import data_path
from src.deserialisers.little_navmap import LittleNavmap


def process():
    """Processes a flight plan file to extract and format waypoint information.

    This function reads a `.lnmpln` flight plan file from a predefined path, deserializes it
    using the `LittleNavmap` class, and formats each waypoint into a structured Python
    representation. The extracted data is printed to the console.

    Steps:
    ------
    1. Locate the flight plan file using the `data_path` function.
    2. Use the `LittleNavmap.read()` method to deserialize the flight plan into a `plan` object.
    3. Iterate over the waypoints in the flight plan.
    4. Format each waypoint with details such as:
        - Name
        - Identifier
        - Type
        - Region
        - Comment (if any)
        - Geographic position (`Lon`, `Lat`, `Alt`).
    5. Print the formatted waypoints to the console as structured Python representations.

    Output Format:
    --------------
    Prints formatted waypoints in the following structure:

    ```python
    Waypoint(
        Name='Waypoint Name',
        Ident='Identifier',
        Type='Some Type',
        Region='Some Region',
        Comment='Optional Comment',
        Pos=Pos(**{
            "@Lon": <Longitude>,
            "@Lat": <Latitude>,
            "@Alt": <Altitude>
        }),
    ),
    ```

    Notes:
    ------
    - The function assumes that the flight plan file exists at the specified location.
    - The function does not return any value; its primary purpose is to print formatted
      waypoint data to the console.

    Example Usage:
    --------------
    Running this function will produce the formatted output of all waypoints in a flight plan.
    Ensure that the `.lnmpln` file is placed in the directory defined by `data_path()`.

    Dependencies:
    -------------
    - `data_path`: A function to locate the directory where the flight plan file is located.
    - `LittleNavmap`: A deserializer that reads `.lnmpln` files and converts them into
      Python objects for further processing.
    """
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
