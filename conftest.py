import sys
from pathlib import Path

# Add the directory to sys.path
sys.path.insert(0, str(Path("/Users/richardlyon/Dev/python-flightplan")))


def data_path() -> Path:
    current_dir = Path(__file__).parent
    test_file_path = current_dir / "tests" / "data"

    return test_file_path
