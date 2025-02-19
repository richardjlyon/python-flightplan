from pprint import pprint
from pydantic import BaseModel, RootModel, Field, model_validator
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


class SimData(RootModel[str]):
    pass


class NavDataValue(RootModel[str]):
    pass


class NavData(BaseModel):
    Cycle: str = Field(alias="@Cycle")
    Value: NavDataValue = Field(alias="#text")

    class Config:
        allow_population_by_field_name = True


class AircraftPerformance(BaseModel):
    FilePath: str
    Type: str
    Name: str


class Pos(BaseModel):
    Lon: float = Field(alias="@Lon")
    Lat: float = Field(alias="@Lat")
    Alt: float = Field(alias="@Alt")


class Waypoint(BaseModel):
    Name: Optional[str] = None
    Ident: str
    Type: str
    Region: Optional[str] = None
    Comment: Optional[str] = None
    Pos: Pos


class Flightplan(BaseModel):
    Header: Header
    SimData: SimData
    NavData: NavData
    AircraftPerformance: AircraftPerformance
    Waypoints: List[Waypoint]

    # Updated Pydantic validator to handle nested Waypoints structure
    @model_validator(mode="before")
    def unwrap_waypoints(cls, values):
        """
        Handle 'Waypoints' if it's a dictionary with a nested 'Waypoint' key.
        """
        waypoints = values.get("Waypoints")
        # Check if Waypoints is a dictionary containing 'Waypoint'
        if isinstance(waypoints, dict) and "Waypoint" in waypoints:
            # Assign the nested list of waypoint dictionaries
            values["Waypoints"] = waypoints["Waypoint"]
        elif waypoints is None:
            # If Waypoints key is missing or None, set it to an empty list
            values["Waypoints"] = []
        return values


class LittleNavmap(BaseModel):
    xmlns_xsi: Optional[str] = Field(alias="@xmlns:xsi")  # Map to `xmlns:xsi` attribute
    xsi_noNamespaceSchemaLocation: Optional[str] = Field(
        alias="@xsi:noNamespaceSchemaLocation"
    )  # Map to `xsi:noNamespaceSchemaLocation` attribute
    Flightplan: Flightplan


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
        print(f"->> Wrapping {len(waypoints)} waypoints for XML serialization.")
        flightplan["Waypoints"] = {
            "Waypoint": waypoints
        }  # Wrap into <Waypoints><Waypoint></Waypoint></Waypoints>
    else:
        print("->> Waypoints is empty or None, not wrapping.")

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


def test_serialization_reversibility(original_xml: str, model: BaseModel) -> bool:
    """
    Test if the serialized XML matches the original XML exactly.
    """
    # Serialize the model back to XML
    serialized_xml = serialize_to_xml(model)

    # Parse original and serialized XML back to dictionaries for comparison
    original_dict = xmltodict.parse(original_xml)
    serialized_dict = xmltodict.parse(serialized_xml)

    # Compare dictionaries
    return original_dict == serialized_dict


# Main parsing logic
def main():
    current_dir = Path(__file__).parent
    test_file_path = (
        current_dir
        / "tests"
        / "data"
        / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    )

    # Read the XML file
    with open(test_file_path, "r", encoding="utf-8") as file:
        xml_content = file.read()

    # Parse XML to a dictionary
    xml_dict = xmltodict.parse(xml_content)

    # Extract "LittleNavmap" as root
    data = xml_dict["LittleNavmap"]

    # Deserialize into the LittleNavmap Pydantic model
    navmap = LittleNavmap(**data)

    # Modify waypoint 1 name
    navmap.Flightplan.Waypoints[1].Ident = "BOLLOCKS"
    # Pretty print the deserialized model
    pprint(navmap.model_dump(), indent=2, width=120, depth=None)

    output_file_path = current_dir / "test.lnmpln"
    serialized_xml = serialize_to_xml(navmap)
    with open(output_file_path, "w") as f:
        f.write(serialized_xml)

    # # Uncomment these lines if you want to test serialization back to XML

    # print("Serialized XML:")
    # print(serialized_xml)
    # is_equal = test_serialization_reversibility(xml_content, navmap)
    # print(f"Original and serialized XML are the same: {is_equal}")


if __name__ == "__main__":
    main()
