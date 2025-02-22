from pathlib import Path
from typing import Tuple

import typer
from typing_extensions import Annotated

from src import get_config_path
from src.deserialisers.little_navmap import LittleNavmap
from src.route_processor.route_processor import process_route
from src.route_processor.processor_config import (
    ProcessorConfig,
    deserialize_from_toml_file,
)


def convert(
    file_path: Annotated[
        Path, typer.Argument(help="The filepath of the file to convert")
    ],
    verbose: bool = False,
):
    """Convert the given plan"""
    typer.echo(f"\nConverting {file_path}")

    # Load the plan and get low level entry and exit points
    plan = load_plan(file_path)
    entry_id, exit_id = get_entry_exit_ids(plan)
    config = generate_config(entry_id, exit_id)
    waypoints = plan.Flightplan.Waypoints
    processed_route_wps = process_route(waypoints, config)
    plan.Flightplan.Waypoints = processed_route_wps
    save_to_disk(file_path, plan)

    # Report
    if verbose:
        report(processed_route_wps)


def report(processed_route_wps):
    print()
    print(f"{'Name':<14} | {'Ident':<15} | {'Alt':<5} | {'Comment':<21}")
    print("-" * 55)
    for wp in processed_route_wps:
        print(
            f"{wp.Name if wp.Name else 'None':14} : {wp.Ident:15} : {wp.Pos.Alt:05} : {wp.Comment}"
        )


def save_to_disk(file_path, plan):
    outfile = file_path.with_name(file_path.stem + " [processed]" + file_path.suffix)
    try:
        plan.write(outfile)
        typer.echo(f"File written to {outfile}")
    except Exception as e:
        typer.echo(f"Error writing file: {e}")
        raise typer.Exit(code=1)


def load_plan(file_path):
    try:
        plan = LittleNavmap.read(file_path)

    except Exception as e:
        typer.echo(f"Error reading file: {e}")
        raise typer.Exit(code=1)
    return plan


def get_entry_exit_ids(plan) -> Tuple[int, int]:
    typer.echo("\nWaypoints in the plan:")
    print(f"{'Index':<6} | {'Name':<14} | {'Ident':<15} | {'Alt':<5} | {'Comment':<21}")
    print("-" * 70)

    for index, wp in enumerate(plan.Flightplan.Waypoints, start=1):
        print(
            f"{index:<6} : {wp.Name if wp.Name else 'None':14} : {wp.Ident:15} : {wp.Pos.Alt:05} : {wp.Comment}"
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


def generate_config(entry_id, exit_id):
    config_path = get_config_path()
    config = deserialize_from_toml_file(ProcessorConfig, config_path)
    config.id_entry = entry_id
    config.id_exit = exit_id
    return config


def validate_index(value: str, min_value: int, max_value: int) -> int:
    """
    Validate that the input is a positive integer.
    """
    try:
        number = int(value)
        if number < min_value or number > max_value:
            raise typer.BadParameter(
                f"The number must be between {min_value} and {max_value}."
            )
        return number

    except ValueError:
        raise typer.BadParameter("Invalid number. Please enter a valid integer.")
