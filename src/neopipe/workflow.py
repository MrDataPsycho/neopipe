
from neopipe.pipeline import SyncPipeline
from neopipe.pipeline import AsyncPipeline
from typing import TypeVar


T = TypeVar("T")
E = TypeVar("E")

class SyncWorkflow(SyncPipeline[T, E]):
    """
    A workflow class that inherits from SyncPipeline, providing the same functionality
    under a different namespace for workflow-oriented use cases.
    """
    pass


class AsyncWorkflow(AsyncPipeline[T, E]):
    """
    A workflow class that inherits from AsyncPipeline, providing the same functionality
    under a different namespace for workflow-oriented use cases.
    """
    pass
