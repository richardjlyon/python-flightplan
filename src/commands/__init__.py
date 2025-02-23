"""This module imports and exports core commands for the FlightPlan CLI application.

Commands available:
- `convert`: Handles the conversion of flight plans by processing route waypoints.
- `config`: Provides configuration management for the FlightPlan application.
"""

from .convert import convert

__all__ = ["convert"]
