"""Pydantic models and functions for XML serialization of LittleNavmap flight plans.

It includes:
1. Pydantic models to represent the structure of flight plans, including headers, waypoints,
   navigation data, simulation data, and aircraft performance specifics.
2. A `read` method to load flight plan data from an XML file.
3. A `write` method to save flight plan data back to XML format.
4. Utility functions to handle XML serialization and cleanup.

The primary purpose of this module is to enable structured and validated data manipulation
for LittleNavmap flight planning software.
"""

from pydantic import BaseModel, RootModel, Field, field_validator
import xmltodict
from pathlib import Path


# Define all models
class Header(BaseModel):
    """Represents the header information for a flight plan.

    Attributes:
        FlightplanType (str): The type of flight plan.
        CruisingAlt (int): The cruising altitude in feet.
        CruisingAltF (float): The cruising altitude as a floating-point value.
        CreationDate (str): The date the flight plan was created.
        FileVersion (str): The version of the flight plan file.
        ProgramName (str): The name of the program that created the flight plan.
        ProgramVersion (str): The version of the program used to create the flight plan.
        Documentation (str): Additional documentation or metadata associated with the flight plan.
    """

    FlightplanType: str
    CruisingAlt: int
    CruisingAltF: float
    CreationDate: str
    FileVersion: str
    ProgramName: str
    ProgramVersion: str
    Documentation: str


class SimDataValue(RootModel[str]):
    """Represents a sim data value."""

    pass


class NavDataValue(RootModel[str]):
    """Represents a nav data value."""

    pass


class SimData(BaseModel):
    """Represents simulation data with a cycle identifier and value.

    Attributes:
        Cycle (str): The simulation cycle, mapped from the "@Cycle" XML attribute.
        Value (SimDataValue): The value of the simulation data, mapped from the "#text" XML element.
    """

    Cycle: str = Field(alias="@Cycle")
    Value: SimDataValue = Field(alias="#text")

    class Config:
        """Configuration class for customizing model behavior.

        Attributes:
            populate_by_name (bool): When set to True, allows population of fields using their aliases.
        """

        populate_by_name = True


class NavData(BaseModel):
    """Represents navigation data with a cycle identifier and value.

    Attributes:
        Cycle (str): The navigation data cycle, mapped from the "@Cycle" XML attribute.
        Value (NavDataValue): The value of the navigation data, mapped from the "#text" XML element.
    """

    Cycle: str = Field(alias="@Cycle")
    Value: NavDataValue = Field(alias="#text")

    class Config:
        """Configuration class for customizing model behavior.

        Attributes:
            populate_by_name (bool): When set to True, allows population of fields using their aliases.
        """

        populate_by_name = True


class AircraftPerformance(BaseModel):
    """Represents the performance characteristics of an aircraft.

    Attributes:
        FilePath (str | None): The file path to the aircraft's performance data, if available.
        Type (str): The type of the aircraft.
        Name (str): The name of the aircraft.
    """

    FilePath: str | None = None
    Type: str
    Name: str


class Pos(BaseModel):
    """Represents the position of an object with longitude, latitude, and altitude.

    Attributes:
        Lon (float): The longitude of the position, mapped from the "@Lon" XML attribute.
        Lat (float): The latitude of the position, mapped from the "@Lat" XML attribute.
        Alt (int): The altitude of the position in integer form, mapped from the "@Alt" XML attribute.

    Methods:
        float_to_int(value): Validates and transforms the altitude (`Alt`) field, converting it to an integer if
                            it's provided as a string or a float.
    """

    Lon: float = Field(alias="@Lon")
    Lat: float = Field(alias="@Lat")
    Alt: int = Field(alias="@Alt")

    class Config:
        """Configuration class for customizing model behavior.

        Attributes:
            populate_by_name (bool): When set to True, allows population of fields using their aliases.
        """

        populate_by_name = True

    @field_validator("Alt", mode="before")  # Transform the value before validation
    def float_to_int(cls, value):
        """Validates and converts the altitude (Alt) value into an integer.

        This method processes the input value for the "Alt" field before any further validation, ensuring that
        string and float values are safely converted into integers.

        Args:
            value (str | float | int): The value to validate and transform.
                                       It can be a string, float, or integer.

        Returns:
            int: The altitude value as an integer.

        Raises:
            ValueError: If the input value is a string that cannot be converted to a float.
        """
        if isinstance(value, str):  # Handle string input
            try:
                value = float(value)  # Convert string to float first
            except ValueError:
                raise ValueError(f"Invalid value for Alt: {value}")
        if isinstance(value, float):  # Convert float to int
            return int(value)
        return value


def __repr__(self):
    return f'Pos(**{{"@Lon": {self.Lon}, "@Lat": {self.Lat}, "@Alt": {self.Alt}}})'


class Waypoint(BaseModel):
    """Represents a waypoint, which is a specific navigational position or marker.

    Attributes:
        Name (str | None): The name of the waypoint. Defaults to None if not provided.
        Ident (str): The identifier for the waypoint.
        Type (str): The type of the waypoint (e.g., navigation point, checkpoint).
        Region (str | None): The region associated with the waypoint. Defaults to None if not provided.
        Comment (str | None): An optional comment or description for the waypoint. Defaults to None.
        Pos (Pos): The positional data of the waypoint (latitude, longitude, altitude).

    Methods:
        __repr__(): Returns a string representation of the Waypoint object for debugging purposes.
    """

    Name: str | None = None
    Ident: str
    Type: str
    Region: str | None = None
    Comment: str | None = None
    Pos: Pos

    def __repr__(self):
        """Provides a formatted string representation of the Waypoint instance.

        This method is primarily used for debugging and outputs all the attributes in
        a readable multi-line format. Attributes like `Region` and `Comment` will display
        `None` if no value is set; otherwise, their content is appropriately quoted.

        Returns:
            str: A multi-line string representation of the Waypoint instance, showing
                 the values of attributes (`Name`, `Ident`, `Type`, `Region`, `Comment`, `Pos`).
        """
        return (
            f"Waypoint(\n"
            f'    Name="{self.Name}",\n'
            f'    Ident="{self.Ident}",\n'
            f'    Type="{self.Type}",\n'
            f"    Region={None if self.Region is None else '"' + self.Region + '"'},\n"
            f"    Comment={None if self.Comment is None else '"' + self.Comment + '"'},\n"
            f"    Pos={repr(self.Pos)},\n"
            f")"
        )


class Flightplan(BaseModel):
    """Represents a complete flight plan.

    Attributes:
        Header (Header): Contains metadata and header details about the flight plan,
                         such as its creation date or formatting.
        SimData (SimData): Stores simulation-specific data, such as information
                           related to the simulator environment.
        NavData (NavData): Represents navigational data used within the flight
                           plan, including routing and other relevant information.
        AircraftPerformance (AircraftPerformance): Contains performance details
                                                   of the aircraft, such as fuel consumption or speed profiles.
        Waypoints (list[Waypoint]): The list of waypoints that define the flight's
                                    route, including their positional and navigational details.
    """

    Header: Header
    SimData: SimData
    NavData: NavData
    AircraftPerformance: AircraftPerformance
    Waypoints: list[Waypoint]


class LittleNavmap(BaseModel):
    """Represents the root model for a Little Navmap flight plan.

    Attributes:
        xmlns_xsi (str | None): Represents the XML namespace for schema instance (`xmlns:xsi` attribute).
                                It is mapped directly to the `@xmlns:xsi` attribute in the source XML.
        xsi_noNamespaceSchemaLocation (str | None): Specifies the location of the schema
                                                    (`xsi:noNamespaceSchemaLocation` attribute).
                                                    It is mapped directly to the `@xsi:noNamespaceSchemaLocation`
                                                    attribute in the source XML.
        Flightplan (Flightplan): Contains the complete flight plan data, including
                                 waypoints, navigation information, aircraft performance,
                                 and relevant metadata.
    """

    xmlns_xsi: str | None = Field(alias="@xmlns:xsi")  # Map to `xmlns:xsi` attribute
    xsi_noNamespaceSchemaLocation: str | None = Field(
        alias="@xsi:noNamespaceSchemaLocation"
    )  # Map to `xsi:noNamespaceSchemaLocation` attribute
    Flightplan: Flightplan

    @classmethod
    def read(cls, file_path: Path) -> "LittleNavmap":
        """Create an instance of LittleNavmap from an XML file.

        Args:
            file_path (str): Path to the XML file.

        Returns:
            LittleNavmap: Instance of LittleNavmap initialized with the contents of the file.
        """
        # Ensure the file exists
        if not file_path.exists():
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        # Parse the XML file
        with file_path.open("r", encoding="utf-8") as file:
            try:
                xml_data = xmltodict.parse(file.read())
            except Exception as e:
                raise ValueError(f"Failed to parse the XML file: {e}")

        # Process the parsed data
        little_navmap_data = xml_data.get("LittleNavmap", {})

        # Fix the nested "Waypoints" field if it exists
        flightplan_data = little_navmap_data.get("Flightplan", {})
        if (
            "Waypoints" in flightplan_data
            and "Waypoint" in flightplan_data["Waypoints"]
        ):
            flightplan_data["Waypoints"] = flightplan_data["Waypoints"]["Waypoint"]

        # Create and return the Flightplan instance
        return cls.model_validate(xml_data.get("LittleNavmap", {}))

    def write(self, file_path: Path) -> None:
        """Write the XML file to disk.

        :param file_path:
        :return: None
        """
        serialized_xml = serialize_to_xml(self)
        with open(file_path, "w") as f:
            try:
                f.write(serialized_xml)
            except Exception as e:
                raise ValueError(f"Failed to write the XML file: {e}")


# Serialization and XML handling
def serialize_to_xml(model: BaseModel) -> str:
    """Serialize a Pydantic model back to an XML string."""
    # Convert Pydantic model to dictionary using aliases
    model_dict = model.model_dump(by_alias=True)

    # Handle Waypoints: Wrapping list as a single dictionary for serialization
    flightplan = model_dict.get("Flightplan", {})
    waypoints = flightplan.get("Waypoints", None)

    if isinstance(waypoints, list):
        flightplan["Waypoints"] = {
            "Waypoint": waypoints
        }  # Wrap into <Waypoints><Waypoint></Waypoint></Waypoints>

    # Remove None values from the entire model dictionary
    model_dict = remove_none_values(model_dict)

    # Wrap everything in the root <LittleNavmap> tag
    xml_dict = {"LittleNavmap": model_dict}

    # Serialize back to XML
    return xmltodict.unparse(xml_dict, pretty=True)


def remove_none_values(obj):
    """Recursively remove keys with None values from a dictionary."""
    if isinstance(obj, dict):
        return {k: remove_none_values(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [remove_none_values(v) for v in obj]
    else:
        return obj
