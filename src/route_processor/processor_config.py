"""
A class for representing processor configuration, and serialising and deserialising it.
"""

import dataclasses
from pathlib import Path
from typing import Optional

import toml


@dataclasses.dataclass
class ProcessorConfig:
    id_entry: Optional[int] = None  # Low Level Entry Point waypoint index
    id_exit: Optional[int] = None  # Low Level Exit Point waypoint index
    route_airspeed_kts: Optional[int] = None  # Low level route airspeed (knots)
    transit_airspeed_kts: int = 495  # Average transit groundspeed @ M0.75
    route_alt_ft: int = 500  # Low Level Route altitude


# Function to serialize the dataclass to a TOML file
def serialize_to_toml_file(
    instance: dataclasses.dataclass,
    file_path: Path,
):
    data_dict = dataclasses.asdict(instance)

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w") as file:
            toml.dump(data_dict, file)
    except Exception as e:
        print("Failed to save configuration file:", e)
        raise


# Function to deserialize a TOML file into a dataclass
def deserialize_from_toml_file(cls, file_path: Path):
    # Check if the file exists
    if not file_path.exists():
        print(f"Configuration file {file_path} not found. Creating a default config...")
        # Create a default instance of the class
        default_instance = cls()
        # Serialize the default instance to a new TOML file
        serialize_to_toml_file(default_instance, file_path)
        return default_instance  # Return the created instance

    # If the file exists, continue with deserialization
    with file_path.open("r") as file:
        data_dict = toml.load(file)

    return cls(**data_dict)
