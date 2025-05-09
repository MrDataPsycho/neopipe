import asyncio
import inspect
import time
import logging
import uuid
from typing import Any, Generic, List, Optional, Tuple, TypeVar

from neopipe.result import (
    Err,
    Result,
    ExecutionResult,
    Trace,
    Traces
)
from neopipe.task import BaseAsyncTask

T = TypeVar("T")  # Input success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Output success type

logger = logging.getLogger(__name__)


class AsyncPipeline(Generic[T, E]):
    """
    An asynchronous pipeline supporting three modes:

    1. run: Concurrent execution of registered tasks, one-to-one with inputs.
    2. run_sequence: Sequential chaining of tasks.
    3. run_parallel: Concurrent execution of multiple pipelines, returning PipelineResult objects.

    Each method supports an optional debug flag to capture per-task traces.

    Tasks must consume and return a Result[T, E].
    """

    def __init__(self, name: Optional[str] = None):
        self.tasks: List[BaseAsyncTask[T, E]] = []
        self.pipeline_id = uuid.uuid4()
        self.name = name or f"AsyncPipeline-{self.pipeline_id}"

    @classmethod
    def from_tasks(
        cls, tasks: List[BaseAsyncTask[T, E]], name: Optional[str] = None
    ) -> "AsyncPipeline[T, E]":
        pipeline = cls(name)
        for task in tasks:
            pipeline.add_task(task)
        return pipeline

    def add_task(self, task: BaseAsyncTask[T, E]) -> None:
        self._validate_task(task)
        self.tasks.append(task)

    def _validate_task(self, task: BaseAsyncTask[T, E]) -> None:
        if not isinstance(task, BaseAsyncTask):
            raise TypeError(f"Only BaseAsyncTask instances allowed, got {type(task)}")
        sig = inspect.signature(task.execute)
        params = [p for p in sig.parameters.values() if p.name != "self"]
        if len(params) != 1:
            raise TypeError(
                f"Task '{task.task_name}' must have exactly one input parameter"
            )
        origin = getattr(params[0].annotation, "__origin__", None)
        if origin is not Result:
            raise TypeError(
                f"Task '{task.task_name}' first arg must be Result[T, E], got {params[0].annotation}"
            )

    async def run(
        self,
        inputs: List[Result[T, E]],
        debug: bool = False
    ) -> ExecutionResult[List[Result[U, E]], E]:
        """
        Execute each task concurrently (1:1 to inputs).
        Returns:
          - .result: List[Result[U,E]]
          - .trace:  None or Trace[List[Result],E]
        """
        if len(inputs) != len(self.tasks):
            return Err("Number of inputs must match number of tasks")

        start = time.perf_counter()
        coros = [task(inp) for task, inp in zip(self.tasks, inputs)]
        try:
            results: List[Result[U, E]] = await asyncio.gather(*coros)
        except Exception as e:
            logger.exception(f"[{self.name}] run() exception")
            return Err(str(e))

        steps: List[Tuple[str, Result[U, E]]] = []
        for task, res in zip(self.tasks, results):
            if debug:
                steps.append((task.task_name, res))
        elapsed = time.perf_counter() - start

        return ExecutionResult(
            result=results,
            trace=Trace(steps=steps) if debug else None,
            execution_time=elapsed
        )

    async def run_sequence(
        self,
        input_result: Result[T, E],
        debug: bool = False
    ) -> ExecutionResult[Result[U, E], E]:
        """
        Run tasks in order, passing Result→Result.
        Returns:
          - .result: the final Result[U,E]
          - .trace:  None or Trace[Result,U,E] of each step
        """
        start = time.perf_counter()
        steps: List[Tuple[str, Result[Any, E]]] = []
        current = input_result

        for task in self.tasks:
            try:
                current = await task(current)
            except Exception as e:
                logger.exception(f"[{self.name}] run_sequence exception in {task.task_name}")
                current = Err(str(e))
            if debug:
                steps.append((task.task_name, current))
            if current.is_err() and not debug:
                break

        elapsed = time.perf_counter() - start
        return ExecutionResult(
            result=current,
            trace=Trace(steps=steps) if debug else None,
            execution_time=elapsed
        )

    @staticmethod
    async def run_parallel(
        pipelines: List["AsyncPipeline[T, E]"],
        inputs: List[Result[T, E]],
        debug: bool = False
    ) -> ExecutionResult[List[Result[U, E]], E]:
        """
        Execute several pipelines concurrently, each with a single input.
        Returns:
          - .result: List[Result[U,E]]
          - .trace:  None or Traces[List[Result],E]
        """
        if len(pipelines) != len(inputs):
            raise AssertionError("Each pipeline needs a corresponding input Result")

        start = time.perf_counter()
        coros = [p.run_sequence(inp, debug) for p, inp in zip(pipelines, inputs)]
        gathered = await asyncio.gather(*coros, return_exceptions=True)

        results: List[Result[U, E]] = []
        traces: List[Trace[U, E]] = []

        for pipeline, exec_res in zip(pipelines, gathered):
            if isinstance(exec_res, Exception):
                # unexpected exception
                err = Err(f"Exception in pipeline '{pipeline.name}': {exec_res}")
                results.append(err)
                if debug:
                    traces.append(Trace(steps=[(pipeline.name, err)]))
                continue

            # exec_res is ExecutionResult[Result[U,E],E]
            assert isinstance(exec_res, ExecutionResult)
            results.append(exec_res.result)
            if debug and exec_res.trace is not None:
                traces.append(exec_res.trace)  # a Trace[T,E]

        elapsed = time.perf_counter() - start
        return ExecutionResult(
            result=results,
            trace=Traces(pipelines=traces) if debug else None,
            execution_time=elapsed
        )

    def __str__(self) -> str:
        names = ", ".join(t.task_name for t in self.tasks)
        return f"{self.name}([{names}])"

    def __repr__(self) -> str:
        return self.__str__()
