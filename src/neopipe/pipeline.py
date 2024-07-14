import inspect
import logging
import uuid
from functools import wraps
from typing import (Any, Callable, List, Self, Type, TypeVar, Union,
                    get_type_hints)

from neopipe.result import Ok, Result
from neopipe.task import ContainerTask, ContainerTaskBase, FunctionTask, Task

logger = logging.getLogger(__name__)

T = TypeVar("T")
E = TypeVar("E")


class Pipeline:
    def __init__(self):
        """Create a Pipeline instance."""
        self.registry: List[Task[Any, Any]] = []
        self.uuid = uuid.uuid4()

    @classmethod
    def from_tasks(cls, tasks: List[Task[T, E]]) -> Self:
        """
        Create a Pipeline instance from a list of Task objects.

        Args:
            tasks (List[Task[Any, Any]]): A list of Task objects.

        Returns:
            Pipeline: A new Pipeline instance.
        """
        for task in tasks:
            if not isinstance(task, Task):
                raise TypeError(f"Only Task objects can be registered but received {type(task)}.")
        pipeline = cls()
        pipeline.registry.extend(tasks)
        return pipeline

    def register(self, retries: int = 1) -> Callable[..., Callable[..., Result[T, E]]]:
        """
        Create a task decorator to register a function or a ContainerTask as a task.

        Args:
            retries (int, optional): The number of times to retry the task. Defaults to 1.

        Returns:
            Callable[..., Callable[..., Result[T, E]]]: A task decorator.
        """
        def decorator(func_or_class: Union[Callable[..., Result[T, E]], Type[ContainerTaskBase]]) -> Callable[..., Result[T, E]]:
            if isinstance(func_or_class, type) and issubclass(func_or_class, ContainerTaskBase):
                task_instance = ContainerTask(func_or_class(), retries=retries)
            elif callable(func_or_class) and inspect.isfunction(func_or_class):
                task_instance = FunctionTask(func_or_class, retries=retries)
            else:
                raise TypeError("Only functions or subclasses of ContainerTaskBase can be registered.")

            self.registry.append(task_instance)

            @wraps(func_or_class)
            def wrapped_func(*args, **kwargs) -> Result[T, E]:
                return task_instance(*args, **kwargs)

            return wrapped_func

        return decorator

    def append_task(self, task: Task[T, E]) -> None:
        """
        Append a Task object, FunctionTask or ContainerTask to the registry.

        Args:
            task (Task[Any, Any]): The task to be appended.

        Returns:
            None
        """
        if not isinstance(task, Task):
            raise TypeError(f"task must be an instance of Task, FunctionTask, or ContainerTask but got {type(task)}.")
        self.registry.append(task)

    def run(self, initial_value: Any, show_progress: bool = False) -> Result[Any, Any]:
        """
        Execute the pipeline with the initial value.

        Args:
            initial_value (Any): The initial value to start the pipeline with.
            show_progress (bool, optional): Whether to show the task completion progress. Defaults to False.

        Returns:
            Result[Any, Any]: The result of the pipeline execution.
        """
        logger.info(f"Pipeline started (UUID: {self.uuid})")
        result = Ok(initial_value)
        total_tasks = len(self.registry)

        for i, task in enumerate(self.registry):
            if result.is_ok():
                result = task(result.unwrap())
                if show_progress:
                    logger.info(f"{i + 1}/{total_tasks} is complete")
                if result.is_err():
                    logger.error(f"Pipeline stopped due to error: {result.error}")
                    return result
        return result


    def show_execution_plan(self) -> None:
        """
        Print the execution plan of the pipeline, showing the sequence of tasks and
        the expected input/output data types.
        """
        if not self.registry:
            print("Pipeline is empty.")
            return

        print("Pipeline Execution Plan:")
        print("=" * 30)
        for i, task in enumerate(self.registry):
            func_name = task.func.__name__ if isinstance(task, FunctionTask) else task.container.__class__.__name__
            type_hints = get_type_hints(task.func if isinstance(task, FunctionTask) else task.container.__call__)
            input_type = list(type_hints.values())[0] if type_hints else 'Any'
            output_type = type_hints.get('return', 'Any')

            print(f"{func_name} : {input_type} -> {output_type}")

            if i < len(self.registry) - 1:
                print(" |")
                print(" V")
        print("=" * 30)

    def __str__(self) -> str:
        """Return a string representation of the pipeline."""
        tasks_str = "\n  ".join(str(task) for task in self.registry)
        return f"Pipeline with {len(self.registry)} tasks:\n  {tasks_str}"

    def __repr__(self) -> str:
        """Return a string representation of the pipeline."""
        return self.__str__()
