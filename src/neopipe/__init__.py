import logging

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Import core components
from neopipe.result import Err, Ok, Result, ExecutionResult, Trace, Traces
from neopipe.task import (
    BaseSyncTask, 
    BaseAsyncTask,
    FunctionSyncTask,
    FunctionAsyncTask,
    ClassSyncTask,
    ClassAsyncTask
)
from neopipe.pipeline import SyncPipeline, AsyncPipeline
from neopipe.workflow import SyncWorkflow, AsyncWorkflow

# Specify what is available for import from this package
__all__ = [
    "Result", "Ok", "Err", "ExecutionResult", "Trace", "Traces",
    "BaseSyncTask", "BaseAsyncTask", "FunctionSyncTask", "FunctionAsyncTask", 
    "ClassSyncTask", "ClassAsyncTask",
    "SyncPipeline", "AsyncPipeline", "SyncWorkflow", "AsyncWorkflow"
]

from .__about__ import __version__
