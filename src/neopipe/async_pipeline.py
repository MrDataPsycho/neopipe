import uuid
import asyncio
import logging
import inspect
from typing import Any, List, Optional, TypeVar, Generic, Tuple, Union
from neopipe.result import Result, Ok, Err, PipelineResult, PipelineTrace, SinglePipelineTrace
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
        cls,
        tasks: List[BaseAsyncTask[T, E]],
        name: Optional[str] = None
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
        params = [p for p in sig.parameters.values() if p.name != 'self']
        if len(params) != 1:
            raise TypeError(f"Task '{task.task_name}' must have exactly one input parameter")
        origin = getattr(params[0].annotation, '__origin__', None)
        if origin is not Result:
            raise TypeError(f"Task '{task.task_name}' first arg must be Result[T, E], got {params[0].annotation}")

    async def run(
        self,
        inputs: List[Result[T, E]],
        debug: bool = False
    ) -> Result[Union[List[U], Tuple[Optional[List[U]], List[Tuple[str, Result[T, E]]]]], E]:
        """
        Concurrently execute registered tasks with matching inputs.

        Returns a list of outputs or a debug trace.
        """
        if len(inputs) != len(self.tasks):
            return Err("Number of inputs must match number of tasks")

        coros = [task(inp) for task, inp in zip(self.tasks, inputs)]
        try:
            results: List[Result[U, E]] = await asyncio.gather(*coros)
        except Exception as e:
            logger.exception(f"[{self.name}] run() exception")
            return Err(str(e))

        trace: List[Tuple[str, Result[T, E]]] = []
        outputs: List[U] = []
        for task, res in zip(self.tasks, results):
            if debug:
                trace.append((task.task_name, res))
            if res.is_err():
                if debug:
                    return Ok((None, trace))
                return res
            outputs.append(res.unwrap())
        return Ok((outputs, trace)) if debug else Ok(outputs)

    async def run_sequence(
        self,
        input_result: Result[T, E],
        debug: bool = False
    ) -> Result[Union[U, Tuple[Optional[U], List[Tuple[str, Result[T, E]]]]], E]:
        """
        Execute registered tasks in sequence.
        """
        trace: List[Tuple[str, Result[Any, E]]] = []
        current: Result[Any, E] = input_result
        for task in self.tasks:
            try:
                res: Result[U, E] = await task(current)
            except Exception as e:
                logger.exception(f"[{self.name}] run_sequence exception in {task.task_name}")
                return Err(str(e))
            trace.append((task.task_name, res))
            if res.is_err():
                if debug:
                    return Ok((None, trace))
                return res
            current = res  # type: ignore
        final = current.unwrap()  # type: ignore
        return Ok((final, trace)) if debug else Ok(final)

    @staticmethod
    async def run_parallel(
        pipelines: List["AsyncPipeline[T, E]"],
        inputs: List[Result[T, E]],
        debug: bool = False
    ) -> Result[Union[List[PipelineResult], Tuple[Optional[List[PipelineResult]], PipelineTrace]], E]:
        """
        Execute multiple pipelines concurrently, each with its own input.

        Returns:
            - debug=False: Ok([PipelineResult, ...]) or Err(first_error)
            - debug=True : Ok((List[PipelineResult], PipelineTrace))
        """
        if len(pipelines) != len(inputs):
            raise AssertionError("Each pipeline must have a corresponding input Result")

        coros = [p.run_sequence(inp, debug) for p, inp in zip(pipelines, inputs)]
        try:
            results = await asyncio.gather(*coros)
        except Exception as e:
            logger.exception("run_parallel exception")
            return Err(str(e))

        pipeline_results: List[PipelineResult] = []
        all_traces: List[SinglePipelineTrace[E]] = []

        for pipeline, res in zip(pipelines, results):
            if res.is_err():
                return res
            if debug:
                val, trace = res.unwrap()
                pipeline_results.append(PipelineResult(name=pipeline.name, result=val))
                all_traces.append(SinglePipelineTrace(name=pipeline.name, tasks=trace))
            else:
                pipeline_results.append(PipelineResult(name=pipeline.name, result=res.unwrap()))

        if debug:
            return Ok((pipeline_results, PipelineTrace(pipelines=all_traces)))
        return Ok(pipeline_results)

    def __str__(self) -> str:
        names = ", ".join(t.task_name for t in self.tasks)
        return f"{self.name}([{names}])"

    def __repr__(self) -> str:
        return self.__str__()
