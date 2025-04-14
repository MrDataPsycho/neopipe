from abc import ABC, abstractmethod
from typing import Callable, Optional, TypeVar, Generic, Awaitable
import uuid
import logging
import time
from neopipe.result import Result, Err
from functools import wraps
import asyncio


T = TypeVar("T")
E = TypeVar("E")

logger = logging.getLogger(__name__)


class BaseSyncTask(ABC, Generic[T, E]):
    """
    Base class for all synchronous tasks.
    Encapsulates retry logic and common metadata (e.g., task_id).
    """

    def __init__(self, retries: int = 1):
        self.retries = retries
        self.task_id = uuid.uuid4()

    def __call__(self, *args, **kwargs) -> Result[T, E]:
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.retries + 1):
            try:
                logger.info(f"[Task {self}] Attempt {attempt}")
                result = self.execute(*args, **kwargs)
                if result.is_ok():
                    logger.info(f"[Task {self}] Success")
                    return result
                else:
                    logger.warning(f"[Task {self}] Failed with Err: {result.err()}")
                    return result
            except Exception as e:
                last_exception = e
                logger.error(f"[Task {self}] Exception: {e}")
                time.sleep(2 ** (attempt - 1))

        return Err(f"[Task {self}] failed after {self.retries} retries: {last_exception}")

    @abstractmethod
    def execute(self, *args, **kwargs) -> Result[T, E]:
        """
        Task execution logic. Must return a Result.
        """
        pass

    def __str__(self):
        return f"{self.__class__.__name__} (ID={self.task_id})"

    def __repr__(self):
        return self.__str__()


class FunctionSyncTask(BaseSyncTask[T, E]):
    """
    Wraps a synchronous function as a retryable task.
    """

    def __init__(self, func: Callable[..., Result[T, E]], retries: int = 1):
        super().__init__(retries)
        self.func = func

    def execute(self, *args, **kwargs) -> Result[T, E]:
        return self.func(*args, **kwargs)

    @classmethod
    def decorator(cls, retries: int = 1) -> Callable[[Callable[..., Result[T, E]]], 'FunctionSyncTask[T, E]']:
        """
        Turns a function into a FunctionSyncTask with the given retry count.

        Example:
            @FunctionSyncTask.decorator(retries=2)
            def compute(x): ...

        Returns:
            FunctionSyncTask instance.
        """
        def wrapper(func: Callable[..., Result[T, E]]) -> 'FunctionSyncTask[T, E]':
            task = cls(func, retries=retries)

            @wraps(func)
            def wrapped_func(*args, **kwargs) -> Result[T, E]:
                return task(*args, **kwargs)

            wrapped_func.task = task  # Optional: expose raw task
            return task

        return wrapper

    def __str__(self):
        return f"FunctionSyncTask({self.func.__name__}, ID={self.task_id})"



class ClassSyncTask(BaseSyncTask[T, E], ABC):
    """
    Base class for defining class-based synchronous tasks.
    You must implement the `execute()` method.
    """

    def __init__(self, retries: int = 1):
        super().__init__(retries)



class BaseAsyncTask(ABC, Generic[T, E]):
    """
    Base class for all asynchronous tasks. Implements retry, logging, and task identity.
    """

    def __init__(self, retries: int = 1):
        self.retries = retries
        self.task_id = uuid.uuid4()

    async def __call__(self, *args, **kwargs) -> Result[T, E]:
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.retries + 1):
            try:
                logger.info(f"[Task {self}] Attempt {attempt}")
                result = await self.execute(*args, **kwargs)
                if result.is_ok():
                    logger.info(f"[Task {self}] Success")
                    return result
                else:
                    logger.warning(f"[Task {self}] Failed with Err: {result.err()}")
                    return result
            except Exception as e:
                last_exception = e
                logger.error(f"[Task {self}] Exception: {e}")
                await asyncio.sleep(2 ** (attempt - 1))

        return Err(f"[Task {self}] failed after {self.retries} retries: {last_exception}")

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Result[T, E]:
        """
        Async task execution logic. Must return a Result.
        """
        pass

    def __str__(self):
        return f"{self.__class__.__name__}(ID={self.task_id})"

    def __repr__(self):
        return self.__str__()


class FunctionAsyncTask(BaseAsyncTask[T, E]):
    """
    Wraps an async function as a retryable task.
    """

    def __init__(self, func: Callable[..., Awaitable[Result[T, E]]], retries: int = 1):
        super().__init__(retries)
        self.func = func

    async def execute(self, *args, **kwargs) -> Result[T, E]:
        return await self.func(*args, **kwargs)

    def __str__(self):
        return f"FunctionAsyncTask({self.func.__name__}, ID={self.task_id})"

    @classmethod
    def decorator(cls, retries: int = 1) -> Callable[[Callable[..., Awaitable[Result[T, E]]]], 'FunctionAsyncTask[T, E]']:
        """
        Turns an async function into a FunctionAsyncTask with retry.

        Example:
            @FunctionAsyncTask.decorator(retries=2)
            async def fetch(...): ...

        Returns:
            FunctionAsyncTask instance.
        """
        def wrapper(func: Callable[..., Awaitable[Result[T, E]]]) -> 'FunctionAsyncTask[T, E]':
            task = cls(func, retries=retries)

            @wraps(func)
            async def wrapped(*args, **kwargs) -> Result[T, E]:
                return await task(*args, **kwargs)

            wrapped.task = task  # Optional reference to internal Task
            return task

        return wrapper


class ClassAsyncTask(BaseAsyncTask[T, E], ABC):
    """
    Base class for class-based async tasks.
    Override `async def execute(self) -> Result[T, E]`
    """

    def __init__(self, retries: int = 1):
        super().__init__(retries)

