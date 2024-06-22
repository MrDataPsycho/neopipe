import logging
from typing import Callable, List, Any, TypeVar
from functools import wraps
from tqdm import tqdm
from neopipe.result import Result, Ok, Err
import time
import uuid

# Initialize logging
logging.basicConfig(level=logging.INFO)

T = TypeVar("T")
E = TypeVar("E")


class Task:
    def __init__(self, func: Callable[..., Result[T, E]], retries: int = 1):
        self.func = func
        self.retries = retries
        self.id = uuid.uuid4()

    def __call__(self, *args, **kwargs) -> Result[T, E]:
        @wraps(self.func)
        def wrapped_func(*args, **kwargs) -> Result[T, E]:
            logging.info(f"Executing task {self.func.__name__} (UUID: {self.id})")
            last_exception = None
            for attempt in range(self.retries):
                try:
                    result = self.func(*args, **kwargs)
                    if result.is_ok():
                        logging.info(
                            f"Task {self.func.__name__} succeeded on attempt {attempt + 1}"
                        )
                        return result
                    else:
                        logging.error(
                            f"Task {self.func.__name__} failed on attempt {attempt + 1}: {result.error}"
                        )
                        return result
                except Exception as e:
                    last_exception = e
                    logging.error(
                        f"Task {self.func.__name__} exception on attempt {attempt + 1}: {str(e)}"
                    )
                    time.sleep(2**attempt)  # Exponential backoff

            return Err(
                f"Task {self.func.__name__} failed after {self.retries} attempts: {str(last_exception)}"
            )

        return wrapped_func(*args, **kwargs)

    def __str__(self):
        return f"Task({self.func.__name__}, retries={self.retries})"

    def __repr__(self):
        return self.__str__()
