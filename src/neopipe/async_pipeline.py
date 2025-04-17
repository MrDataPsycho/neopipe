import uuid
import asyncio
import logging
import inspect
from typing import Any, List, Optional, TypeVar, Generic, Tuple, Union
from neopipe.result import Result, Ok, Err
from neopipe.task import BaseAsyncTask

T = TypeVar("T")  # Input success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Output success type

logger = logging.getLogger(__name__)


class AsyncPipeline(Generic[T, E]):
    """
    An asynchronous pipeline that runs a list of BaseAsyncTask instances concurrently,
    matching each task 1-to-1 with the provided input Results.

    Tasks are validated on registration to ensure they accept a Result[T, E].
    Supports an optional debug flag to capture per-task traces.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize an AsyncPipeline.

        Args:
            name: Optional human-readable name for logging/debug.
        """
        self.tasks: List[BaseAsyncTask[T, E]] = []
        self.pipeline_id = uuid.uuid4()
        self.name = name or f"AsyncPipeline-{self.pipeline_id}"

    @classmethod
    def from_tasks(
        cls,
        tasks: List[BaseAsyncTask[T, E]],
        name: Optional[str] = None
    ) -> "AsyncPipeline[T, E]":
        """
        Create a pipeline from a list of tasks.

        Args:
            tasks: List of BaseAsyncTask instances.
            name: Optional pipeline name.

        Returns:
            Configured AsyncPipeline.
        """
        pipeline = cls(name)
        for task in tasks:
            pipeline.add_task(task)
        return pipeline

    def add_task(self, task: BaseAsyncTask[T, E]) -> None:
        """
        Register a new task for concurrent execution.

        Args:
            task: A BaseAsyncTask instance.

        Raises:
            TypeError: If `task` is not a BaseAsyncTask or has invalid signature.
        """
        self._validate_task(task)
        self.tasks.append(task)

    def _validate_task(self, task: BaseAsyncTask[T, E]) -> None:
        """
        Ensure the task has an `execute(self, Result[T, E])` signature.

        Raises:
            TypeError: If validation fails.
        """
        if not isinstance(task, BaseAsyncTask):
            raise TypeError(f"Only BaseAsyncTask instances allowed, got {type(task)}")
        sig = inspect.signature(task.execute)
        params = [p for p in sig.parameters.values() if p.name != 'self']
        if len(params) != 1:
            raise TypeError(
                f"Task '{task.task_name}' must have exactly one input parameter: Result[T, E]"
            )
        param = params[0]
        origin = getattr(param.annotation, '__origin__', None)
        if origin is not Result:
            raise TypeError(
                f"Task '{task.task_name}' first arg must be Result[T, E], found {param.annotation}"
            )

    async def run(
        self,
        inputs: List[Result[T, E]],
        debug: bool = False
    ) -> Result[
        Union[List[U], Tuple[Optional[List[U]], List[Tuple[str, Result[T, E]]]]],
        E
    ]:
        """
        Execute all registered tasks concurrently on their respective inputs.

        Args:
            inputs: list of Result[T, E], same length as tasks.
            debug: if True, returns Ok((outputs, trace)) or Ok((None, trace)) on Err.

        Returns:
            - debug=False: Ok(list_of_unwrapped_outputs) or Err(first_error)
            - debug=True : Ok((outputs, trace_list)) or Ok((None, trace_list)) on first Err
        """
        if len(inputs) != len(self.tasks):
            return Err("Number of inputs must match number of tasks")

        # Launch all tasks concurrently
        coros = [task(inp) for task, inp in zip(self.tasks, inputs)]
        try:
            results: List[Result[U, E]] = await asyncio.gather(*coros)
        except Exception as e:
            logger.exception(f"[{self.name}] Unhandled exception in AsyncPipeline.run")
            return Err(str(e))

        trace: List[Tuple[str, Result[T, E]]] = []
        outputs: List[U] = []

        for task, res in zip(self.tasks, results):
            if debug:
                trace.append((task.task_name, res))
            if res.is_err():
                logger.error(f"[{self.name}] Task {task.task_name} failed: {res.err()}")
                return Ok((None, trace)) if debug else res
            outputs.append(res.unwrap())

        return Ok((outputs, trace)) if debug else Ok(outputs)

    def __str__(self) -> str:
        """Simple repr listing task names."""
        names = ", ".join(t.task_name for t in self.tasks)
        return f"{self.name}([{names}])"

    def __repr__(self) -> str:
        return self.__str__()
