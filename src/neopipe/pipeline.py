import logging
from typing import Callable, List, Any, TypeVar, Self
from functools import wraps
from neopipe.result import Result, Ok
from tqdm import tqdm
from neopipe.task import Task


logger = logging.getLogger(__name__)

T = TypeVar("T")
E = TypeVar("E")

class Pipeline:
    def __init__(self):
        """Create a Pipeline instance."""
        self.registry: List[Callable[..., Result[Any, Any]]] = []

    @classmethod
    def from_tasks(cls, tasks: List[Task]) -> Self:
        """
        Create a Pipeline instance from a list of Task objects.

        Args:
            tasks (List[Task]): A list of Task objects.

        Returns:
            Pipeline: A new Pipeline instance.
        """
        pipeline = cls()
        pipeline.registry.extend(tasks)
        return pipeline

    def register(self, retries: int = 1) -> Callable[..., Callable[..., Result[T, E]]]:
        """
        Create a task decorator to register a function as a task.

        Args:
            retries (int, optional): The number of times to retry the task. Defaults to 1.

        Returns:
            Callable[..., Callable[..., Result[T, E]]]: A task decorator.
        """
        def decorator(func: Callable[..., Result[T, E]]) -> Callable[..., Result[T, E]]:
            task_instance = Task(func, retries=retries)
            self.registry.append(task_instance)

            @wraps(func)
            def wrapped_func(*args, **kwargs) -> Result[T, E]:
                return task_instance(*args, **kwargs)

            return wrapped_func

        return decorator

    def append_function_to_registry(
        self, func: Callable[..., Result[T, E]], retries: int = 1
    ) -> None:
        """
        Append a function as a task to the registry.

        Args:
            func (Callable[..., Result[T, E]]): The function to be appended as a task.
            retries (int, optional): The number of times to retry the task. Defaults to 1.

        Returns:
            None
        """
        task_instance = Task(func, retries=retries)
        self.registry.append(task_instance)

    def append_task_to_registry(self, task: Task) -> None:
        """
        Append a Task object to the registry.

        Args:
            task (Task): The task to be appended.

        Returns:
            None
        """
        if not isinstance(task, Task):
            raise ValueError(
                "task must be an instance of Task not a {}".format(type(task))
            )
        self.registry.append(task)

    def run(self, initial_value: Any, show_progress: bool = False) -> Result:
        """
        Execute the pipeline with the initial value.

        Args:
            initial_value (Any): The initial value to start the pipeline with.
            show_progress (bool, optional): Whether to show a progress bar. Defaults to False.

        Returns:
            Result: The result of the pipeline execution.
        """
        result = Ok(initial_value)
        task_iter = (
            self.registry
            if not show_progress
            else tqdm(
                self.registry,
                desc="Pipeline Progress",
                bar_format="{l_bar}{bar} [ {elapsed} ]",
            )
        )

        for task in task_iter:
            if result.is_ok():
                result = task(result.value)
                if result.is_err():
                    logger.error(f"Pipeline stopped due to error: {result.error}")
                    return result
        return result

    def print_execution_plan(self) -> None:
        """
        Print the execution plan of the pipeline, showing the sequence of tasks and 
        the expected input/output data types.
        """
        if not self.registry:
            print("Pipeline is empty.")
            return

        print("Pipeline Execution Plan:")
        print("="*30)
        for i, task in enumerate(self.registry):
            func_name = task.func.__name__
            input_type = task.func.__annotations__.get('return', 'Any')
            output_type = list(task.func.__annotations__.values())[0] if task.func.__annotations__ else 'Any'
            
            print(f"{func_name} : {output_type} -> {input_type}")
            
            if i < len(self.registry) - 1:
                print(" |")
                print(" |")
                print(" V")
        print("="*30)


    def __str__(self) -> str:
        """Return a string representation of the pipeline."""
        tasks_str = "\n  ".join(str(task) for task in self.registry)
        return f"Pipeline with {len(self.registry)} tasks:\n  {tasks_str}"

    def __repr__(self) -> str:
        """Return a string representation of the pipeline."""
        return self.__str__()
