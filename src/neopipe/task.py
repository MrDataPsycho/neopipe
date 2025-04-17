import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from functools import wraps
from typing import Awaitable, Callable, Generic, Optional, Self, TypeVar

from neopipe.result import Err, Result

T = TypeVar("T")  # Input success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Output success type

logger = logging.getLogger(__name__)


class BaseSyncTask(ABC, Generic[T, E]):
    """
    Abstract base class for synchronous tasks that operate entirely on Result[T, E].

    Each task receives a Result object, processes it (if Ok), and returns a new Result.
    Retry logic, logging, and task identification are handled automatically.

    Attributes:
        retries (int): Number of retry attempts if execution fails.
        task_id (UUID): Unique identifier for the task instance.
    """

    def __init__(self, retries: int = 1):
        self.retries = retries
        self.task_id = uuid.uuid4()

    @property
    def task_name(self) -> str:
        """Returns a human-readable task name."""
        return self.__class__.__name__

    def __call__(self, input_result: Result[T, E]) -> Result[U, E]:
        """
        Executes the task with retry logic.

        Args:
            input_result (Result[T, E]): The input wrapped in a Result.

        Returns:
            Result[U, E]: The result of the task, either Ok or Err.
        """
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.retries + 1):
            try:
                logger.info(
                    f"[{self.task_name}] Attempt {attempt} - Task ID: {self.task_id}"
                )
                result = self.execute(input_result)

                if result.is_ok():
                    logger.info(f"[{self.task_name}] Success on attempt {attempt}")
                    return result
                else:
                    logger.warning(f"[{self.task_name}] Returned Err: {result.err()}")
                    return result

            except Exception as e:
                last_exception = e
                logger.error(f"[{self.task_name}] Exception: {e}")
                time.sleep(2 ** (attempt - 1))  # Exponential backoff

        return Err(
            f"[{self.task_name}] failed after {self.retries} retries: {last_exception}"
        )

    @abstractmethod
    def execute(self, input_result: Result[T, E]) -> Result[U, E]:
        """
        Override this method in subclasses or function wrappers.

        Args:
            input_result (Result[T, E]): The input wrapped in a Result.

        Returns:
            Result[U, E]: The transformed output.
        """
        pass

    def __str__(self) -> str:
        return f"{self.task_name}(ID={self.task_id})"

    def __repr__(self) -> str:
        return self.__str__()


class FunctionSyncTask(BaseSyncTask[T, E]):
    """
    Wraps a function that takes a Result[T, E] and returns a Result[U, E].

    Can be used as a decorator with automatic retry and logging support.
    """

    def __init__(self, func: Callable[[Result[T, E]], Result[U, E]], retries: int = 1):
        super().__init__(retries)
        self.func = func

    @property
    def task_name(self) -> str:
        return self.func.__name__

    def execute(self, input_result: Result[T, E]) -> Result[U, E]:
        return self.func(input_result)

    @classmethod
    def decorator(cls, retries: int = 1):
        """
        A decorator for converting a function into a retryable FunctionSyncTask.

        Example:
            @FunctionSyncTask.decorator(retries=2)
            def process(result: Result[int, str]) -> Result[int, str]:
                ...

        Args:
            retries (int): Number of retry attempts.

        Returns:
            Callable: A decorator that wraps the function in a FunctionSyncTask.
        """

        def wrapper(func: Callable[[Result[T, E]], Result[U, E]]) -> Self:
            task = cls(func, retries)

            @wraps(func)
            def wrapped(input_result: Result[T, E]) -> Result[U, E]:
                return task(input_result)

            wrapped.task = task  # Optional: attach task instance
            return task

        return wrapper

    def __str__(self):
        return f"FunctionSyncTask({self.task_name}, ID={self.task_id})"


class ClassSyncTask(BaseSyncTask[T, E], ABC):
    """
    Extend this class to create stateful or configurable sync tasks.

    You must override the `execute(self, input_result: Result[T, E])` method.

    Example:
        class MultiplyTask(ClassSyncTask[int, str]):
            def __init__(self, factor: int):
                super().__init__()
                self.factor = factor

            def execute(self, input_result: Result[int, str]) -> Result[int, str]:
                if input_result.is_ok():
                    return Ok(input_result.unwrap() * self.factor)
                return input_result
    """

    def __init__(self, retries: int = 1):
        super().__init__(retries)


class BaseAsyncTask(ABC, Generic[T, E]):
    """
    Abstract base class for async tasks that operate entirely on Result[T, E].

    Each task receives a Result, processes it (if Ok), and returns a new Result.
    """

    def __init__(self, retries: int = 1):
        self.retries = retries
        self.task_id = uuid.uuid4()

    @property
    def task_name(self) -> str:
        """Returns a human-readable task name."""
        return self.__class__.__name__

    async def __call__(self, input_result: Result[T, E]) -> Result[U, E]:
        """
        Executes the task with retry logic.

        Args:
            input_result (Result[T, E]): The input Result from a previous task.

        Returns:
            Result[U, E]: Final task result after retry handling.
        """
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.retries + 1):
            try:
                logger.info(
                    f"[{self.task_name}] Attempt {attempt} - Task ID: {self.task_id}"
                )
                result = await self.execute(input_result)

                if result.is_ok():
                    logger.info(f"[{self.task_name}] Success on attempt {attempt}")
                    return result
                else:
                    logger.warning(f"[{self.task_name}] Returned Err: {result.err()}")
                    return result

            except Exception as e:
                last_exception = e
                logger.error(f"[{self.task_name}] Exception: {e}")
                await asyncio.sleep(2 ** (attempt - 1))  # exponential backoff

        return Err(
            f"[{self.task_name}] failed after {self.retries} retries: {last_exception}"
        )

    @abstractmethod
    async def execute(self, input_result: Result[T, E]) -> Result[U, E]:
        """
        Async task execution logic that must be overridden.

        Args:
            input_result (Result[T, E]): The input Result.

        Returns:
            Result[U, E]: The output Result.
        """
        pass

    def __str__(self) -> str:
        return f"{self.task_name}(ID={self.task_id})"

    def __repr__(self) -> str:
        return self.__str__()


class FunctionAsyncTask(BaseAsyncTask[T, E]):
    """
    Wraps an async function that takes a Result[T, E] and returns a Result[U, E].
    """

    def __init__(
        self, func: Callable[[Result[T, E]], Awaitable[Result[U, E]]], retries: int = 1
    ):
        super().__init__(retries)
        self.func = func

    @property
    def task_name(self) -> str:
        return self.func.__name__

    async def execute(self, input_result: Result[T, E]) -> Result[U, E]:
        return await self.func(input_result)

    @classmethod
    def decorator(cls, retries: int = 1):
        """
        A decorator for turning an async function into a FunctionAsyncTask.

        Example:
            @FunctionAsyncTask.decorator(retries=2)
            async def fetch(result: Result[str, str]) -> Result[str, str]:
                ...

        Returns:
            FunctionAsyncTask[T, E]
        """

        def wrapper(func: Callable[[Result[T, E]], Awaitable[Result[U, E]]]) -> Self:
            task = cls(func, retries)

            @wraps(func)
            async def wrapped(input_result: Result[T, E]) -> Result[U, E]:
                return await task(input_result)

            wrapped.task = task
            return task

        return wrapper

    def __str__(self):
        return f"FunctionAsyncTask({self.task_name}, ID={self.task_id})"


class ClassAsyncTask(BaseAsyncTask[T, E], ABC):
    """
    Extend this class to define custom async tasks that operate on Result[T, E].

    Example:
        class MultiplyTask(ClassAsyncTask[int, str]):
            def __init__(self, factor: int):
                super().__init__()
                self.factor = factor

            async def execute(self, input_result: Result[int, str]) -> Result[int, str]:
                if input_result.is_ok():
                    return Ok(input_result.unwrap() * self.factor)
                return input_result
    """

    def __init__(self, retries: int = 1):
        super().__init__(retries)
