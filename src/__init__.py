"""This module provides utility functions for handling application configuration paths.

The primary function, `get_config_path`, determines the appropriate file path for the
application's configuration file, either from a user-specified location or from
the system's default application directory.
"""

from pathlib import Path

import typer

app_name = "FlightPlan"


def get_config_path(user_path: Path | None = None) -> Path:
    """Return the location of the application configuration file.

    If a user-specified path is provided, it will use that path. Otherwise, it defaults
    to the application directory for the FlightPlan app.

    Args:
        user_path (Path, optional): Custom file path for the configuration file. Defaults to None.

    Returns:
        Path: The resolved file path for the application configuration file.
    """
    return user_path or Path(typer.get_app_dir(app_name)) / "config.toml"
