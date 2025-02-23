"""The convert command."""

from pathlib import Path
from typing import Annotated

import typer

from src.deserialisers.little_navmap import LittleNavmap, Waypoint
from src.route_processor.route_processor import ProcessorConfig, process_route


def convert(
    file_path: Annotated[
        Path,
        typer.Argument(help="The filepath of the file to convert"),
    ],
    transit_airspeed_kts: Annotated[
        int,
        typer.Option(help="Transit airspeed in knots"),
    ] = 495,
    route_airspeed_kts: Annotated[
        int,
        typer.Option(help="Low level airspeed in knots"),
    ] = 420,
    *,
    verbose: bool = False,
) -> None:
    """Converts the input flight plan file by processing defined routes and waypoints.

    Parameters:
        file_path (Path): The filepath of the flight plan file to convert.
        transit_airspeed_kts (int): The transit airspeed in knots (default is 495).
        route_airspeed_kts (int): The low-level route airspeed in knots (default is 420).
        verbose (bool): If True, outputs additional details about the processed route.

    Returns:
        None
    """
    typer.echo(f"\nConverting {file_path}")

    # Load the plan and get low level entry and exit points
    plan = load_plan(file_path)
    waypoints = plan.Flightplan.Waypoints

    entry_id, exit_id = get_entry_exit_ids(plan)

    config = ProcessorConfig(
        id_entry=entry_id,
        id_exit=exit_id,
        route_airspeed_kts=route_airspeed_kts,
        transit_airspeed_kts=transit_airspeed_kts,
    )

    processed_route_wps = process_route(waypoints, config)

    plan.Flightplan.Waypoints = processed_route_wps
    save_to_disk(file_path, plan)

    # Report
    if verbose:
        report(processed_route_wps)


def report(processed_route_wps: list[Waypoint]) -> None:
    """Displays a detailed report of the processed waypoints.

    Parameters:
        processed_route_wps (list): A list of waypoints, each containing name, identifier, altitude, and comments.

    Returns:
        None
    """
    typer.echo()
    typer.echo(f"{'Name':<14} | {'Ident':<15} | {'Alt':<5} | {'Comment':<21}")
    typer.echo("-" * 55)
    for wp in processed_route_wps:
        typer.echo(
            f"{wp.Name if wp.Name else 'None':14} : {wp.Ident:15} : {wp.Pos.Alt:05} : {wp.Comment}",
        )


def save_to_disk(file_path: Path, plan: LittleNavmap) -> None:
    """Saves the updated flight plan to disk.

    Parameters:
        file_path (Path): The original filepath of the flight plan.
        plan: The processed flight plan object to save.

    Raises:
        typer.Exit: If an error occurs during the file write operation.

    Returns:
        None
    """
    outfile = file_path.with_name(file_path.stem + " [processed]" + file_path.suffix)
    try:
        plan.write(outfile)
        typer.echo(f"File written to {outfile}")
    except Exception as e:
        typer.echo(f"Error writing file: {e}")
        raise typer.Exit(code=1) from e


def load_plan(file_path: Path) -> LittleNavmap:
    """Reads and loads the flight plan file.

    Parameters:
        file_path (Path): The filepath of the flight plan file.

    Raises:
        typer.Exit: If an error occurs during the file read operation.

    Returns:
        plan: The loaded flight plan object.
    """
    try:
        plan = LittleNavmap.read(file_path)

    except Exception as e:
        typer.echo(f"Error reading file: {e}")
        raise typer.Exit(code=1) from e
    return plan


def get_entry_exit_ids(plan: LittleNavmap) -> tuple[int, int]:
    """Prompts the user to select entry and exit waypoint indices for route processing.

    Parameters:
        plan: The loaded flight plan object containing waypoints.

    Returns:
        tuple[int, int]: The indices of the selected entry and exit waypoints.

    Notes:
        The function validates user input to ensure values are within the range of available waypoint indices.
    """
    typer.echo("\nWaypoints in the plan:")
    typer.echo(
        f"{'Index':<6} | {'Name':<14} | {'Ident':<15} | {'Alt':<5} | {'Comment':<21}",
    )
    typer.echo("-" * 70)

    for index, wp in enumerate(plan.Flightplan.Waypoints, start=1):
        typer.echo(
            f"{index:<6} : {wp.Name if wp.Name else 'None':14} : {wp.Ident:15} : {wp.Pos.Alt:05} : {wp.Comment}",
        )

    max_index = len(plan.Flightplan.Waypoints)

    typer.echo()
    entry_idx = typer.prompt(
        f"Low level entry point waypoint index (1..{max_index})",
        value_proc=lambda v: validate_index(v, 1, max_index),
    )
    exit_idx = typer.prompt(
        f"Low level entry point waypoint index (1..{max_index})",
        value_proc=lambda v: validate_index(v, entry_idx + 1, max_index),
    )

    return entry_idx, exit_idx


def validate_index(value: str, min_value: int, max_value: int) -> int:
    """Validates and converts a string input to an integer within the specified range.

    Parameters:
        value (str): The input value to validate.
        min_value (int): The minimum allowed value.
        max_value (int): The maximum allowed value.

    Returns:
        int: The validated and converted value.

    Raises:
        typer.BadParameter: If the input is not a valid integer or is out of range.
    """
    try:
        number = int(value)
        if number < min_value or number > max_value:
            raise typer.BadParameter(
                f"The number must be between {min_value} and {max_value}.",
            )
        return number

    except ValueError:
        raise typer.BadParameter(
            "Invalid number. Please enter a valid integer.",
        ) from None
