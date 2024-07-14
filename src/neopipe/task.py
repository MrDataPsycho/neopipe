import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar

from neopipe.result import Err, Ok, Result

logger = logging.getLogger(__name__)

T = TypeVar("T")
E = TypeVar("E")

class Task(Generic[T, E]):
    """Base Task class."""

    def __call__(self, *args: Any, **kwargs: Any) -> Result[T, E]:
        raise NotImplementedError("Subclasses should implement this method")


class FunctionTask(Task[T, E]):
    """Task wrapper for a function."""

    def __init__(self, func: Callable[..., Result[T, E]], retries: int = 1):
        self.func = func
        self.retries = retries

    def __call__(self, *args: Any, **kwargs: Any) -> Result[T, E]:
        last_exception = None
        for attempt in range(self.retries):
            try:
                result = self.func(*args, **kwargs)
                if result.is_ok():
                    logger.info(
                        f"Function {self.func.__name__} succeeded on attempt {attempt + 1}"
                    )
                    return result
                else:
                    logger.error(
                        f"Function {self.func.__name__} failed on attempt {attempt + 1}: {result.error}"
                    )
                    return result
            except Exception as e:
                last_exception = e
                logger.error(
                    f"Function {self.func.__name__} exception on attempt {attempt + 1}: {str(e)}"
                )
                time.sleep(2**attempt)  # Exponential backoff

        return Err(
            f"Function {self.func.__name__} failed after {self.retries} attempts: {str(last_exception)}"
        )


class ContainerTaskBase(ABC, Task[T, E]):
    """Abstract base class for container tasks."""

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Result[T, E]:
        pass


class ContainerTask(Task[T, E]):
    """Task wrapper for a ContainerTask instance."""

    def __init__(self, container: ContainerTaskBase, retries: int = 1):
        self.container = container
        self.retries = retries

    def __call__(self, *args: Any, **kwargs: Any) -> Result[T, E]:
        last_exception = None
        for attempt in range(self.retries):
            try:
                result = self.container(*args, **kwargs)
                if result.is_ok():
                    logger.info(
                        f"Container {self.container.__class__.__name__} succeeded on attempt {attempt + 1}"
                    )
                    return result
                else:
                    logger.error(
                        f"Container {self.container.__class__.__name__} failed on attempt {attempt + 1}: {result.error}"
                    )
                    return result
            except Exception as e:
                last_exception = e
                logger.error(
                    f"Container {self.container.__class__.__name__} exception on attempt {attempt + 1}: {str(e)}"
                )
                time.sleep(2**attempt)  # Exponential backoff

        return Err(
            f"Container {self.container.__class__.__name__} failed after {self.retries} attempts: {str(last_exception)}"
        )
