import logging

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# # Import necessary modules
from .result import Result, Ok, Err
# from .task import AsyncTask, SyncTask, AbstractAsyncTask, AbstractSyncTask
# from .pipeline import Pipeline


# Specify what is available for import from this package
__all__ = ['Result', 'Ok', 'Err']

from .__about__ import __version__
