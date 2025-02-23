"""Handles computing jet climb and descent performance for a given flight level."""

import os
from enum import Enum
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field


class JetOperation(Enum):
    """Enum to represent climb, descent, and cruise operations."""

    NORMAL_CLIMB = "normal_climb"
    NAV_DESCENT = "nav_descent"
    LL_CRUISE = "ll_cruise"
    ML_CRUISE = "ml_cruise"


class ClimbDescentPerformanceData(BaseModel):
    """Represents performance data for aircraft climb or descent operations.

    This model includes information about the distance traveled, time taken,
    fuel consumed, and the type of operation (climb or descent).

    Attributes:
        distance_nm (float): The distance traveled during the operation in nautical miles.
                             Must be greater than 0.
        time_secs (int): The time taken for the operation in seconds.
                         Must be 0 or greater.
        fuel_kg (float): The amount of fuel consumed during the operation in kilograms.
                         Must be 0 or greater.
        operation (JetOperation): The type of operation performed, either "CLIMB" or "DESCENT".
                                  Defined by the `JetOperation` enum.

    Config:
        use_enum_values (bool): Enables the use of enum values directly for validation.

    Notes:
        - Validation ensures that `distance_nm` is greater than 0,
          `time_secs` is 0 or greater, and `fuel_kg` is 0 or greater.
        - The `JetOperation` enum defines the valid values for the `operation` field.
    """

    distance_nm: float = Field(
        ...,
        gt=0,
        description="Distance traveled in nautical miles; must be greater than 0.",
    )
    time_secs: int = Field(
        ...,
        ge=0,
        description="Time taken in seconds; must be at least 0.",
    )
    fuel_kg: float = Field(
        ...,
        ge=0,
        description="Fuel used in kilograms; must be at least 0.",
    )
    operation: JetOperation = Field(
        ...,
        description="The type of operation, either 'CLIMB' or 'DESCENT'.",
    )

    class Config:
        """Configuration class for Pydantic models.

        Attributes:
            use_enum_values (bool): When set to `True`, the values of Enum fields
                                    are used directly instead of the Enum instances.
                                    This simplifies validation and serialization
                                    by automatically converting Enum instances to
                                    their corresponding values.

        Purpose:
            - This configuration is used in Pydantic models to customize behavior.
            - By enabling `use_enum_values`, any fields that use Enums will store their
              values directly rather than the Enum objects, making it easier to work
              with them in JSON serialization or other data transformations.
        """

        use_enum_values = (
            True  # Allows enum values to be used directly for validation purposes
        )


class LLCruisePerformanceData(BaseModel):
    """Represents low level cruise performance data."""

    kg_min: float = Field(
        ...,
        ge=0,
        description="Fuel consumption kg/min; must be at least 0.",
    )
    operation: JetOperation = Field(
        ...,
        description="The type of operation, either 'CLIMB' or 'DESCENT'.",
    )


class MLCruisePerformanceData(BaseModel):
    """Represents medium level cruise performance data."""

    kg_min: float = Field(
        ...,
        ge=0,
        description="Fuel consumption kg/min; must be at least 0.",
    )
    kg_anm: float = Field(
        ...,
        ge=0,
        description="Fuel consumption kg/anm; must be at least 0.",
    )
    operation: JetOperation = Field(
        ...,
        description="The type of operation, either 'CLIMB' or 'DESCENT'.",
    )


def get_climb_descent_performance_data(
    operation: JetOperation,
    flight_level: int,
) -> ClimbDescentPerformanceData:
    """Retrieves climb or descent performance data for a given operation and flight level.

    This function processes data related to aircraft climb or descent operations,
    extracts the relevant performance metrics, and returns them as a
    `ClimbDescentPerformanceData` object.

    Args:
        operation (JetOperation): The type of operation to retrieve data for.
                                  Can be either "CLIMB" or "DESCENT".
        flight_level (int): The flight level (in hundreds of feet) for which performance data
                            will be retrieved. For example, a flight level of 330 represents 33,000 feet.

    Returns:
        ClimbDescentPerformanceData: A data object containing performance information
                                     including distance traveled, time taken, fuel consumed,
                                     and the operation type.

    Process:
        1. Loads a pre-defined data source for the given operation using the `load_df` function.
        2. Transforms and prepares the dataframe, including:
           - Converting time values into seconds using `mmss_to_seconds`.
           - Dropping unnecessary columns and sorting by flight level.
        3. Searches the dataset for the specified `flight_level` using the `lookup_fl` function.
        4. Constructs a `ClimbDescentPerformanceData` object with the retrieved performance metrics.

    Notes:
        - The function assumes that the `load_df` function loads data based on the operation type.
        - The `mmss_to_seconds` helper converts time recorded in "MM:SS" format into seconds.
        - The `lookup_fl` helper retrieves performance data corresponding to the flight level.

    Raises:
        - An error may occur if the `flight_level` is not found in the dataset.
        - Validation errors may occur when constructing the `ClimbDescentPerformanceData` object
          if the data does not meet the model's constraints.

    Example:
        ```python
        performance_data = get_climb_descent_performance_data(JetOperation.CLIMB, 330)
        print(performance_data)
        # Output: ClimbDescentPerformanceData containing metrics for climb at FL330.
        ```
    """
    df = load_df(operation)

    # Prepare the dataframe
    df["time_secs"] = df["time"].apply(mmss_to_seconds)
    df = df.drop(columns=["time"])
    df = df.sort_values(by="fl").reset_index(drop=True)

    result = lookup_fl(df, flight_level)

    # Create and return a PerformanceData object
    return ClimbDescentPerformanceData(
        distance_nm=result["distance_nm"],
        time_secs=result["time_secs"],
        fuel_kg=result["fuel_kg"],
        operation=operation,
    )


def get_ll_cruise_performance_data(
    operation: JetOperation,
    speed_kts: int,
) -> LLCruisePerformanceData:
    """Retrieves low-level cruise performance data for a given operation and airspeed.

    This function processes data to fetch performance metrics related to low-level cruise
    operations at a specified airspeed and returns them as an `LLCruisePerformanceData` object.

    Args:
        operation (JetOperation): The type of operation to retrieve data for.
                                  Typically represents a low-level cruise operation.
        speed_kts (int): The true airspeed in knots for which performance data will be retrieved.

    Returns:
        LLCruisePerformanceData: A data object containing cruise performance information,
                                 including fuel consumption rate (`kg_min`) and the operation type.

    Process:
        1. Loads cruise data for the given operation using the `load_df` function.
        2. Sorts the data by airspeed (`kts`).
        3. Searches for the entry corresponding to the specified `speed_kts` using the `lookup_kts` function.
        4. Constructs an `LLCruisePerformanceData` object with the retrieved fuel consumption rate
           and the operation type.

    Notes:
        - The function assumes that the dataset contains airspeed (`kts`) and fuel consumption (`kg_min`) fields.
        - The `lookup_kts` helper function retrieves performance data for the closest match to the specified airspeed.

    Raises:
        - An error may occur if the `speed_kts` is not found in the dataset or lies outside the supported range.
        - Validation errors may occur when creating the `LLCruisePerformanceData` object if input data is invalid.

    Example:
        ```python
        cruise_data = get_ll_cruise_performance_data(JetOperation.CRUISE, 250)
        print(cruise_data)
        # Output: LLCruisePerformanceData containing metrics for cruise at 250 knots airspeed.
        ```
    """
    df = load_df(operation)
    df = df.sort_values(by="kts").reset_index(drop=True)
    result = lookup_kts(df, speed_kts)

    return LLCruisePerformanceData(
        kg_min=result["kg_min"],
        operation=operation,
    )


def get_ml_cruise_performance_data(
    operation: JetOperation,
    flight_level: int,
) -> MLCruisePerformanceData:
    """Retrieves mid-level cruise performance data for a given operation and flight level.

    This function processes data to derive performance metrics related to mid-level cruise
    operations at a specified flight level and returns them as an `MLCruisePerformanceData` object.

    Args:
        operation (JetOperation): The type of operation to retrieve data for,
                                  typically for mid-level cruise operations.
        flight_level (int): The flight level (in hundreds of feet) for which performance data
                            will be obtained. For instance, FL300 represents 30,000 feet.

    Returns:
        MLCruisePerformanceData: A data object containing mid-level cruise performance metrics,
                                 including:
                                 - Fuel consumption rate (`kg_min`) in kilograms per minute.
                                 - Fuel efficiency (`kg_anm`) in kilograms per nautical mile.
                                 - The operation type.

    Process:
        1. Loads cruise performance data based on the operation using the `load_df` function.
        2. Sorts the dataset by flight level (`fl`).
        3. Searches for the entry corresponding to the specified flight level using the `lookup_fl` function.
        4. Constructs and returns an `MLCruisePerformanceData` object, with key metrics rounded to two decimal places.

    Notes:
        - Fuel consumption (`kg_min`) and fuel efficiency (`kg_anm`) are rounded to enhance precision.
        - The function assumes that the dataset contains `fl`, `kg_min`, and `kg_anm` fields.
        - The `lookup_fl` helper function is used to retrieve metrics specific to the given flight level.

    Raises:
        - An error may occur if the specified `flight_level` is not found in the dataset or lies outside the supported range.
        - Validation errors may occur when constructing the `MLCruisePerformanceData` object if the input data fails validation.

    Example:
        ```python
        cruise_data = get_ml_cruise_performance_data(JetOperation.CRUISE, 300)
        print(cruise_data)
        # Output: MLCruisePerformanceData containing metrics for cruise at FL300.
        ```
    """
    df = load_df(operation)
    df = df.sort_values(by="fl").reset_index(drop=True)
    result = lookup_fl(df, flight_level)

    return MLCruisePerformanceData(
        kg_min=round(result["kg_min"], 2),
        kg_anm=round(result["kg_anm"], 2),
        operation=operation,
    )


def load_df(operation: JetOperation) -> pd.DataFrame:
    """Loads performance data for a given operation from a CSV file.

    This function dynamically locates and loads the CSV file associated with the
    specified operation type. It returns the data as a Pandas DataFrame for further processing.

    Args:
        operation (JetOperation): An enumeration representing the type of operation
                                  (e.g., "CLIMB", "DESCENT", "CRUISE").
                                  The CSV file is named based on the operation type.

    Returns:
        pandas.DataFrame: A DataFrame containing the loaded performance data.

    Process:
        1. Constructs the file path dynamically based on the `operation` value.
           - The file is expected to reside in a "performance_data" subdirectory
             relative to the current file's location.
           - The file name is structured as `<operation>_performance.csv`, where
             `<operation>` is the lowercase value of the `operation` enum.
        2. Verifies the existence of the file.
           - If the file is not found, a `FileNotFoundError` is raised.
        3. Attempts to load the file using Pandas' `read_csv` function.
           - If the file cannot be read because of file format or other issues,
             a `ValueError` is raised with the specific error information.

    Raises:
        FileNotFoundError: If the expected CSV file does not exist at the derived location.
        ValueError: If there is an error while reading the CSV file (e.g., invalid file format).

    Notes:
        - The directory in which the CSV files are stored is `performance_data` under the
          current script's directory.
        - This function assumes that the `operation` value is an instance of an appropriate
          Enum class (e.g., `JetOperation`) with a `value` attribute.

    Example:
        ```python
        from enum import Enum


        # Example JetOperation enum
        class JetOperation(Enum):
            CLIMB = "climb"
            DESCENT = "descent"
            CRUISE = "cruise"


        # Load data for the "climb" operation
        df = load_df(JetOperation.CLIMB)
        print(df.head())
        # Output: Displays the first few rows of the loaded DataFrame.
        ```
    """
    current_file_directory = Path(__file__).parent
    file_name = f"{operation.value.lower()}_performance.csv"
    file_path = current_file_directory / "performance_data" / file_name
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Performance data file not found: {file_path}")
    # Load the CSV data
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}") from e
    return df


def lookup_fl(df: pd.DataFrame, flight_level: int) -> pd.DataFrame:
    """Looks up or interpolates performance data for a specified flight level.

    The function retrieves the performance data corresponding to the given `flight_level`
    from the input DataFrame. If the exact flight level is not present, it interpolates
    values using linear interpolation to estimate the missing data.

    Args:
        df (pandas.DataFrame): The DataFrame containing performance data.
                               It must include a column labeled `"fl"` (flight level).
        flight_level (int): The flight level (in hundreds of feet) for which performance data
                            is requested. For example, a flight level of 300 corresponds to 30,000 feet.

    Returns:
        pandas.DataFrame: A DataFrame containing the row of interpolated or matched data
                          for the specified flight level.

    Process:
        1. Checks if the `flight_level` exists in the `"fl"` column of the input DataFrame.
           - If the flight level exists, it fetches the corresponding row.
           - If the flight level is missing, linear interpolation is performed.
             - The function adds the missing `flight_level` to the index.
             - Linear interpolation is applied across the DataFrame to calculate
               missing values for the new row.
        2. Retrieves the row corresponding to the requested flight level after ensuring
           it exists in the DataFrame.
        3. Returns the resulting row as a single-row DataFrame.

    Raises:
        ValueError: If the interpolation fails to generate valid data for the given
                    flight level (e.g., outside the bounds of available data).

    Notes:
        - The interpolation process relies on Pandas' `interpolate` function with
          the `linear` method, ensuring smooth transitions between data points.
        - `limit_direction="both"` ensures interpolation works for data at both ends
          of the dataset if the flight level is outside the range of the existing data.

    Example:
        ```python
        import pandas as pd

        # Example DataFrame
        data = {"fl": [280, 290, 310, 320], "fuel_kg": [1000, 1100, 1200, 1300]}
        df = pd.DataFrame(data)

        # Lookup for flight level 300 (missing in the DataFrame)
        result = lookup_fl(df, 300)
        print(result)
        # Output: A DataFrame row with interpolated values for flight level 300
        ```
    """
    if flight_level not in df["fl"].values:
        # Interpolate values for the missing flight level
        df = (
            df.set_index("fl").reindex([*df["fl"].tolist(), flight_level]).sort_index()
        )  # Add and sort index with the new flight level
        df = df.interpolate(method="linear", limit_direction="both").reset_index()

    # Extract the row for the requested flight level
    result_row = df.loc[df["fl"] == flight_level]
    if result_row.empty:
        raise ValueError(f"Unable to interpolate data for flight level {flight_level}")

    return result_row


def lookup_kts(df: pd.DataFrame, speed_kts: int) -> pd.DataFrame:
    """Looks up or interpolates performance data for a specified airspeed in knots.

    The function retrieves the performance data corresponding to the given `speed_kts`
    (true airspeed in knots) from the input DataFrame. If the exact airspeed is not present
    in the data, it uses linear interpolation to estimate the missing data.

    Args:
        df (pandas.DataFrame): The DataFrame containing performance data.
                               It must include a column labeled `"kts"` (true airspeed in knots).
        speed_kts (int): The airspeed, in knots, for which performance data is requested.

    Returns:
        pandas.DataFrame: A DataFrame containing the row of interpolated or matched data
                          for the specified airspeed.

    Process:
        1. Checks if the `speed_kts` exists in the `"kts"` column of the input DataFrame.
           - If the airspeed exists, retrieves the corresponding row.
           - If the airspeed is missing, linear interpolation is applied:
             - Adds the missing `speed_kts` to the index of the DataFrame.
             - Performs linear interpolation to calculate missing values at the requested airspeed.
        2. Retrieves the row of performance data corresponding to the requested airspeed.
        3. Returns the resulting row as a single-row DataFrame.

    Raises:
        ValueError: If interpolation fails or no data can be determined for the given airspeed.

    Notes:
        - The interpolation utilizes Pandas' `interpolate` method with the `linear` method
          to estimate values for the missing airspeed.
        - Airspeeds listed in the `"kts"` column must follow a reasonable numerical order
          for interpolation to work accurately.
        - The `limit_direction="both"` option ensures interpolation is applied for airspeeds
          outside the range of available values when necessary.

    Example:
        ```python
        import pandas as pd

        # Example DataFrame
        data = {"kts": [100, 150, 200, 250], "fuel_kg": [500, 450, 400, 350]}
        df = pd.DataFrame(data)

        # Lookup for airspeed 175 knots (missing from the DataFrame)
        result = lookup_kts(df, 175)
        print(result)
        # Output: A DataFrame row with interpolated values for 175 knots
        ```
    """
    if speed_kts not in df["kts"].values:
        # Interpolate values for the missing airspeed
        df = (
            df.set_index("kts").reindex([*df["kts"].tolist(), speed_kts]).sort_index()
        )  # Add and sort index with the new airspeed
        df = df.interpolate(method="linear", limit_direction="both").reset_index()

    # Extract the row for the requested flight level
    result_row = df.loc[df["kts"] == speed_kts]
    if result_row.empty:
        raise ValueError(f"Unable to interpolate data for flight level {speed_kts}")

    return result_row


def mmss_to_seconds(time_str: str) -> int:
    """Converts a time string in "MM:SS" format to total seconds.

    The function parses a time string in the "MM:SS" format, where "MM" represents
    minutes and "SS" represents seconds, and returns the total time in seconds.

    Args:
        time_str (str): A string representing time in the format "MM:SS".
                        - Example: "02:30" represents 2 minutes and 30 seconds.

    Returns:
        int: The total time in seconds, calculated as (minutes * 60) + seconds.
        None: If the input string is invalid (e.g., not in "MM:SS" format or contains
              non-numeric values).

    Process:
        1. Splits the input string into minutes and seconds based on the colon delimiter `:`.
           Both components are expected to be integers.
        2. Converts minutes to seconds (`minutes * 60`) and adds the seconds.
        3. Returns the total number of seconds.
        4. If parsing fails (e.g., invalid format or non-numeric values), the function
           returns `None`.

    Raises:
        ValueError: This exception is caught internally if the input cannot be split into
                    two integers, ensuring the function handles invalid inputs gracefully.

    Notes:
        - The input string must strictly follow the "MM:SS" format.
        - Invalid inputs, such as non-numeric strings or incorrectly formatted strings
          (e.g., "2.30", "123", or "MM:SS:FF"), will result in `None` being returned.

    Example:
        ```python
        # Convert "02:30" to seconds
        result = mmss_to_seconds("02:30")
        print(result)  # Output: 150

        # Convert invalid time string
        result = mmss_to_seconds("invalid")
        print(result)  # Output: None
        ```
    """
    try:
        minutes, seconds = map(int, time_str.split(":"))
        return minutes * 60 + seconds
    except ValueError:
        return None  # Handle bad input gracefully (you can also raise an error instead)
