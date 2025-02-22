import sys
from pathlib import Path

# Add the root project directory to sys.path because python is absurd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer

from src.commands import convert, config

app = typer.Typer(
    help="Use one of the commands below. Type [COMMAND] --help for more info."
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Show the help message if no command is provided.
    """
    if ctx.invoked_subcommand is None:  # If no subcommand is invoked
        typer.echo(ctx.get_help())  # Display the help message
        raise typer.Exit()  # Exit the program


app.command()(convert)
app.command()(config)

if __name__ == "__main__":
    app()
