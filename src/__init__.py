from pathlib import Path
import typer

app_name = "FlightPlan"


def get_config_path(user_path: Path = None) -> Path:
    """Return the location of the application configuration file."""
    return user_path or Path(typer.get_app_dir(app_name)) / "config.toml"
