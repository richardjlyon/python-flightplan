"""This module handles serialisation adn deserialisation of LittleNavmap flight plans."""

from pydantic import BaseModel, RootModel, Field
from typing import List, Optional
import xmltodict
from pathlib import Path


# Define all models
class Header(BaseModel):
    FlightplanType: str
    CruisingAlt: int
    CruisingAltF: float
    CreationDate: str
    FileVersion: str
    ProgramName: str
    ProgramVersion: str
    Documentation: str


class SimDataValue(RootModel[str]):
    pass


class NavDataValue(RootModel[str]):
    pass


class SimData(BaseModel):
    Cycle: str = Field(alias="@Cycle")
    Value: SimDataValue = Field(alias="#text")

    class Config:
        populate_by_name = True


class NavData(BaseModel):
    Cycle: str = Field(alias="@Cycle")
    Value: NavDataValue = Field(alias="#text")

    class Config:
        populate_by_name = True


class AircraftPerformance(BaseModel):
    FilePath: Optional[str] = None
    Type: str
    Name: str


class Pos(BaseModel):
    Lon: float = Field(alias="@Lon")
    Lat: float = Field(alias="@Lat")
    Alt: float = Field(alias="@Alt")

    class Config:
        populate_by_name = True

    def __repr__(self):
        return f'Pos(**{{"@Lon": {self.Lon}, "@Lat": {self.Lat}, "@Alt": {self.Alt}}})'


class Waypoint(BaseModel):
    Name: Optional[str] = None
    Ident: str
    Type: str
    Region: Optional[str] = None
    Comment: Optional[str] = None
    Pos: Pos

    def __repr__(self):
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
    Header: Header
    SimData: SimData
    NavData: NavData
    AircraftPerformance: AircraftPerformance
    Waypoints: List[Waypoint]


class LittleNavmap(BaseModel):
    xmlns_xsi: Optional[str] = Field(alias="@xmlns:xsi")  # Map to `xmlns:xsi` attribute
    xsi_noNamespaceSchemaLocation: Optional[str] = Field(
        alias="@xsi:noNamespaceSchemaLocation"
    )  # Map to `xsi:noNamespaceSchemaLocation` attribute
    Flightplan: Flightplan

    @classmethod
    def read(cls, file_path: Path) -> "LittleNavmap":
        """
        Create an instance of LittleNavmap from an XML file.

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
        """
        Write the XML file to disk.

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
    """
    Serialize a Pydantic model back to an XML string.
    """
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
    """
    Recursively remove keys with None values from a dictionary.
    """
    if isinstance(obj, dict):
        return {k: remove_none_values(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [remove_none_values(v) for v in obj]
    else:
        return obj
