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
    An asynchronous pipeline supporting three modes:

    1. `run`: Concurrent execution of registered tasks, one-to-one with inputs.
    2. `run_sequence`: Sequential chaining of tasks, passing each output to the next.
    3. `run_parallel`: Concurrent execution of multiple pipelines.

    Each method supports an optional `debug` flag to capture per-task traces.

    Tasks must consume and return a `Result[T, E]`.
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
            An AsyncPipeline with tasks registered.
        """
        pipeline = cls(name)
        for task in tasks:
            pipeline.add_task(task)
        return pipeline

    def add_task(self, task: BaseAsyncTask[T, E]) -> None:
        """
        Register a new task for later execution.

        Args:
            task: A BaseAsyncTask instance.

        Raises:
            TypeError: If `task` is not a BaseAsyncTask or has invalid signature.
        """
        self._validate_task(task)
        self.tasks.append(task)

    def _validate_task(self, task: BaseAsyncTask[T, E]) -> None:
        """
        Ensure the task defines `execute(self, Result[T, E])`.

        Raises:
            TypeError: on invalid signature.
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
    ) -> Result[Union[List[U], Tuple[Optional[List[U]], List[Tuple[str, Result[T, E]]]]], E]:
        """
        Concurrently execute registered tasks with matching inputs.

        Args:
            inputs: list of Result[T, E], same length as tasks.
            debug: if True, return Ok((outputs, trace)) or Ok((None, trace)) on Err.

        Returns:
            - debug=False: Ok(list_of_unwrapped_outputs) or Err(first_error)
            - debug=True : Ok((outputs, trace)) or Ok((None, trace))
        """
        if len(inputs) != len(self.tasks):
            return Err("Number of inputs must match number of tasks")

        # Launch all tasks concurrently
        coros = [task(inp) for task, inp in zip(self.tasks, inputs)]
        try:
            results: List[Result[U, E]] = await asyncio.gather(*coros)
        except Exception as e:
            logger.exception(f"[{self.name}] Unhandled exception in run()")
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

    async def run_sequence(
        self,
        input_result: Result[T, E],
        debug: bool = False
    ) -> Result[Union[U, Tuple[Optional[U], List[Tuple[str, Result[T, E]]]]], E]:
        """
        Execute registered tasks sequentially, passing each Result to the next.

        Args:
            input_result: initial Result[T, E]
            debug: if True, return Ok((final, trace)) or Ok((None, trace)) on Err.

        Returns:
            - debug=False: Ok(final_value) or Err(error)
            - debug=True: Ok((final or None, trace))
        """
        trace: List[Tuple[str, Result[Any, E]]] = []
        current: Result[Any, E] = input_result

        for task in self.tasks:
            try:
                res: Result[U, E] = await task(current)
            except Exception as e:
                logger.exception(f"[{self.name}] Exception in run_sequence for {task.task_name}")
                return Err(str(e))

            trace.append((task.task_name, res))
            if res.is_err():
                logger.error(f"[{self.name}] Task {task.task_name} failed: {res.err()}")
                return Ok((None, trace)) if debug else res
            current = res  # type: ignore

        final = current.unwrap()  # type: ignore
        return Ok((final, trace)) if debug else Ok(final)  # type: ignore

    @staticmethod
    async def run_parallel(
        pipelines: List["AsyncPipeline[T, E]"],
        inputs: List[Result[T, E]],
        debug: bool = False
    ) -> Result[Union[List[Any], Tuple[Optional[List[Any]], List[Tuple[str, Result[Any, E]]]]], E]:
        """
        Execute multiple pipelines concurrently, each with its own input.

        Args:
            pipelines: list of AsyncPipeline instances.
            inputs:    list of Result[T, E], one per pipeline.
            debug:     if True, return Ok((all_outputs, combined_trace)).

        Returns:
            - debug=False: Ok([out1, out2, ...]) or Err(first_error)
            - debug=True : Ok((outputs, trace))
        """
        if len(pipelines) != len(inputs):
            return Err("Each pipeline must have a corresponding input Result")

        coros = [p.run_sequence(inp, debug) for p, inp in zip(pipelines, inputs)]
        try:
            results = await asyncio.gather(*coros)
        except Exception as e:
            logger.exception("Unhandled exception in run_parallel")
            return Err(str(e))

        outputs: List[Any] = []
        combined_trace: List[Tuple[str, Result[Any, E]]] = []

        for pipeline, res in zip(pipelines, results):
            if res.is_err():
                return res
            if debug:
                val, trace = res.unwrap()
                outputs.append(val)
                combined_trace.extend(trace)
            else:
                outputs.append(res.unwrap())

        return Ok((outputs, combined_trace)) if debug else Ok(outputs)

    def __str__(self) -> str:
        names = ", ".join(t.task_name for t in self.tasks)
        return f"{self.name}([{names}])"

    def __repr__(self) -> str:
        return self.__str__()
