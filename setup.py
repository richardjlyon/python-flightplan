"""Setup script for the python_flightplan package.

This script defines the package metadata and configuration necessary to package and distribute
the python_flightplan project. The project helps with flight plan processing and
low-level navigation utilities for Little Navmap plans.
"""

from setuptools import find_packages, setup

setup(
    # The name of the package to be distributed
    name="python_flightplan",
    # The current version of the package
    version="0.1",
    # Automatically find and include all Python packages in the project
    packages=find_packages(),
    # Include any additional files specified in MANIFEST.in
    include_package_data=True,
)
