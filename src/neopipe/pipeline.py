import logging
from typing import Callable, List, Any, TypeVar
from functools import wraps
import time
from neopipe.result import Result, Ok, Err


# Initialize logging
logging.basicConfig(level=logging.INFO)

T = TypeVar('T')
E = TypeVar('E')


class Pipeline:
    def __init__(self):
        self.tasks: List[Callable[..., Result[Any, Any]]] = []

    def task(self, retries: int = 1) -> Callable[..., Callable[..., Result[T, E]]]:
        def decorator(func: Callable[..., Result[T, E]]) -> Callable[..., Result[T, E]]:
            @wraps(func)
            def wrapped_func(*args, **kwargs) -> Result[T, E]:
                last_exception = None
                for attempt in range(retries):
                    try:
                        result = func(*args, **kwargs)
                        if result.is_ok():
                            logging.info(f"Task {func.__name__} succeeded on attempt {attempt + 1}")
                            return result
                        else:
                            logging.error(f"Task {func.__name__} failed on attempt {attempt + 1}: {result.error}")
                            return result
                    except Exception as e:
                        last_exception = e
                        logging.error(f"Task {func.__name__} exception on attempt {attempt + 1}: {str(e)}")
                        time.sleep(2 ** attempt)  # Exponential backoff

                return Err(f"Task {func.__name__} failed after {retries} attempts: {str(last_exception)}")

            self.tasks.append(wrapped_func)
            return wrapped_func

        return decorator

    def run(self, initial_value: Any) -> Result:
        result = Ok(initial_value)
        for task in self.tasks:
            if result.is_ok():
                result = task(result.value)
                if result.is_err():
                    logging.error(f"Pipeline stopped due to error: {result.error}")
                    return result
        return result
