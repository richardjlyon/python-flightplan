from pathlib import Path

import typer
import toml

from src import get_config_path
from src.route_processor.processor_config import ProcessorConfig, serialize_to_toml_file


def config():
    """Display the path to the configuration file"""
    config_path = get_config_path()
    typer.echo(f"Configuration file: {config_path}")

    # # if the file exists, prompt the user to overwrite
    # if config_path.exists():
    #     response = typer.confirm(
    #         f"The file {config_path} already exists. Do you want to overwrite it?"
    #     )
    #     if response:
    #         typer.echo("Overwriting the existing configuration file...")
    #     else:
    #         typer.echo("Operation canceled.")
    #         return
    #
    # config = ProcessorConfig()
    #
    # try:
    #     serialize_to_toml_file(config, config_path)
    #     typer.echo(f"Configuration saved to {config_path}")
    # except Exception as e:
    #     typer.echo(f"Error saving configuration file: {e}")
    #     raise typer.Exit(code=1)
