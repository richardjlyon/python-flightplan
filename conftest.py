"""Utilities for pytest."""

import sys
from pathlib import Path

# Add the directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def data_path() -> Path:
    """Get the path of the data directory used for test files."""
    current_dir = Path(__file__).parent
    test_file_path = current_dir / "tests" / "data"

    return test_file_path
