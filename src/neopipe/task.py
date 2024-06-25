import logging
from typing import Callable, TypeVar
from functools import wraps
from neopipe.result import Result, Err
import time
import uuid

logger = logging.getLogger(__name__)

T = TypeVar("T")
E = TypeVar("E")


class Task:
    """Task is a wrapper around a function that can be retried."""
    def __init__(self, func: Callable[..., Result[T, E]], retries: int = 1):
        """
        Task is a wrapper around a function that can be retried.

        Args:
            func (Callable[..., Result[T, E]]): _description_
            retries (int, optional): _description_. Defaults to 1.
        """
        self.func = func
        self.retries = retries
        self.id = uuid.uuid4()

    def __call__(self, *args, **kwargs) -> Result[T, E]:
        """
        Execute the task and retry if it fails.

        Returns:
            Result[T, E]: The result of the task
        """
        @wraps(self.func)
        def wrapped_func(*args, **kwargs) -> Result[T, E]:
            logger.info(f"Executing task {self.func.__name__} (UUID: {self.id})")
            last_exception = None
            for attempt in range(self.retries):
                try:
                    result = self.func(*args, **kwargs)
                    if result.is_ok():
                        logger.info(
                            f"Task {self.func.__name__} succeeded on attempt {attempt + 1}"
                        )
                        return result
                    else:
                        logger.error(
                            f"Task {self.func.__name__} failed on attempt {attempt + 1}: {result.error}"
                        )
                        return result
                except Exception as e:
                    last_exception = e
                    logger.error(
                        f"Task {self.func.__name__} exception on attempt {attempt + 1}: {str(e)}"
                    )
                    time.sleep(2**attempt)  # Exponential backoff

            return Err(
                f"Task {self.func.__name__} failed after {self.retries} attempts: {str(last_exception)}"
            )

        return wrapped_func(*args, **kwargs)

    def __str__(self):
        """Return a string representation of the task."""
        return f"Task({self.func.__name__}, retries={self.retries})"

    def __repr__(self):
        """Return a string representation of the task."""
        return self.__str__()
