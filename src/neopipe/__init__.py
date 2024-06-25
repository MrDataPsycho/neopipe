import logging

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Import necessary modules
from .pipeline import Pipeline
from .result import Result, Ok, Err
from .task import Task

# Specify what is available for import from this package
__all__ = ['Pipeline', 'Result', 'Ok', 'Err', 'Task']

from .__about__ import __version__