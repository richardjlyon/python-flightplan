from pathlib import Path

import typer
from typing_extensions import Annotated

from src.deserialisers.little_navmap import LittleNavmap
from src.route_processor.route_processor import ProcessorConfig, process_route

app = typer.Typer()


@app.command()
def convert(
    file_path: Annotated[
        Path, typer.Argument(help="The filepath of the file to convert")
    ],
    verbose: bool = False,
):
    """Convert the given plan."""
    print(f"Converting {file_path}")

    try:
        plan = LittleNavmap.read(file_path)
    except Exception as e:
        typer.echo(f"Error reading file: {e}")
        raise typer.Exit(code=1)

    # Proces the route
    waypoints = plan.Flightplan.Waypoints
    config = ProcessorConfig(id_entry=3, id_exit=12)
    processed_route_wps = process_route(waypoints, config)

    # Create new plan
    plan.Flightplan.Waypoints = processed_route_wps

    # Save to disk
    outfile = file_path.with_name(file_path.stem + " [processed]" + file_path.suffix)
    try:
        plan.write(outfile)
        typer.echo(f"File written to {outfile}")
    except Exception as e:
        typer.echo(f"Error writing file: {e}")
        raise typer.Exit(code=1)

    # Report
    if verbose:
        print()
        print(f"{'Name':<14} | {'Ident':<15} | {'Alt':<5} | {'Comment':<21}")
        print("-" * 55)
        for wp in processed_route_wps:
            print(
                f"{wp.Name if wp.Name else 'None':14} : {wp.Ident:15} : {wp.Pos.Alt:05} : {wp.Comment}"
            )


if __name__ == "__main__":
    app()
