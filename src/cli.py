"""This module serves as the entry point for the FlightPlan CLI application.

It defines a Typer application with multiple subcommands to perform route conversion
and configuration management. Use `--help` with any command to explore its options.
"""

import sys
from pathlib import Path

# Add the root project directory to sys.path because python is absurd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer

from src.commands import convert

app = typer.Typer(
    help="Use one of the commands below. Type [COMMAND] --help for more info."
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Show the help message if no command is provided.

    Args:
        ctx (typer.Context): Typer context object containing information about
                             the current CLI invocation and options.
    """
    if ctx.invoked_subcommand is None:  # If no subcommand is invoked
        typer.echo(ctx.get_help())  # Display the help message
        raise typer.Exit()  # Exit the program


app.command()(convert)

if __name__ == "__main__":
    app()
