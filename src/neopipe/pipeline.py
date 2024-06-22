import logging
from typing import Callable, List, Any, TypeVar, Self
from functools import wraps
import time
from neopipe.result import Result, Ok, Err
from tqdm import tqdm
from neopipe.task import Task


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
    
    def append_function_as_task(self, func: Callable[..., Result[T, E]], retries: int = 1) -> None:
        """
        Append a task to the pipeline.
        """
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


    def run(self, initial_value: Any, show_progress: bool = False) -> Result:
        result = Ok(initial_value)
        task_iter = self.tasks if not show_progress else tqdm(self.tasks, desc="Pipeline Progress", bar_format="{l_bar}{bar} [ {elapsed} ]")

        for task in task_iter:
            if result.is_ok():
                result = task(result.value)
                if result.is_err():
                    logging.error(f"Pipeline stopped due to error: {result.error}")
                    return result
        return result

    
    def from_tasks(cls, tasks: List[Task]) -> Self:
        """
        Create a Pipeline instance from a list of Task objects.
        """
        pipeline = cls()
        pipeline.tasks.extend(tasks)
        return pipeline
    
    def append_task(self, task: Task) -> None:
        """
        Append a Task object to the pipeline.
        """
        if not isinstance(task, Task):
            raise ValueError("task must be an instance of Task not a {}".format(type(task)))
        self.tasks.append(task)