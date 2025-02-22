import sys
from pathlib import Path

# Add the root project directory to sys.path because python is absurd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer

from src.commands import convert

app = typer.Typer()

app.command()(convert)

if __name__ == "__main__":
    app()
