"""
Handles computing jet climb and descent performance for a given flight level.
"""

from pathlib import Path

from pydantic import BaseModel, Field
from enum import Enum
import os
import pandas as pd


class JetOperation(Enum):
    """Enum to represent climb and descent operations."""

    NORMALCLIMB = "normal_climb"
    NAVDESCENT = "nav_descent"


class PerformanceData(BaseModel):
    """
    Represents performance data with validation.
    Includes distance, time (in seconds), and fuel in kilograms.
    """

    distance_nm: float = Field(
        ...,
        gt=0,
        description="Distance traveled in nautical miles; must be greater than 0.",
    )
    time_secs: int = Field(
        ..., ge=0, description="Time taken in seconds; must be at least 0."
    )
    fuel_kg: float = Field(
        ..., ge=0, description="Fuel used in kilograms; must be at least 0."
    )
    operation: JetOperation = Field(
        ..., description="The type of operation, either 'CLIMB' or 'DESCENT'."
    )

    class Config:
        use_enum_values = (
            True  # Allows enum values to be used directly for validation purposes
        )


def get_performance_data(operation: JetOperation, flight_level: int) -> PerformanceData:
    # Define the data file path based on the operation
    current_file_directory = Path(__file__).parent
    file_name = f"{operation.value.lower()}_performance.csv"
    file_path = current_file_directory / "performance_data" / file_name

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Performance data file not found: {file_path}")

    # Load the CSV data
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

    # Prepare the dataframe
    df["time_secs"] = df["time"].apply(mmss_to_seconds)
    df = df.drop(columns=["time"])
    df = df.sort_values(by="fl").reset_index(drop=True)

    result = lookup(df, flight_level)

    # Create and return a PerformanceData object
    return PerformanceData(
        distance_nm=result["distance_nm"],
        time_secs=result["time_secs"],
        fuel_kg=result["fuel_kg"],
        operation=operation,
    )


def lookup(df, flight_level):
    if flight_level not in df["fl"].values:
        # Interpolate values for the missing flight level
        df = (
            df.set_index("fl").reindex(df["fl"].tolist() + [flight_level]).sort_index()
        )  # Add and sort index with the new flight level
        df = df.interpolate(method="linear", limit_direction="both").reset_index()
    # Extract the row for the requested flight level
    result_row = df.loc[df["fl"] == flight_level]
    if result_row.empty:
        raise ValueError(f"Unable to interpolate data for flight level {flight_level}")
    return result_row


def mmss_to_seconds(time_str):
    try:
        minutes, seconds = map(int, time_str.split(":"))
        return minutes * 60 + seconds
    except ValueError:
        return None  # Handle bad input gracefully (you can also raise an error instead)
