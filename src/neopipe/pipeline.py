import inspect
import logging
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generic, List, Optional, Tuple, TypeVar, get_origin

from neopipe.result import (
    Err,
    Result,
    Trace,
    Traces,
    ExecutionResult
)


from neopipe.task import BaseSyncTask

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")

logger = logging.getLogger(__name__)


class SyncPipeline(Generic[T, E]):
    """
    A pipeline that executes BaseSyncTasks sequentially, passing Result[T, E] through each step.

    Attributes:
        tasks (List[BaseSyncTask]): Registered tasks.
        pipeline_id (UUID): Unique ID for the pipeline.
        name (str): Optional name for logging/debugging.
    """

    def __init__(self, name: Optional[str] = None):
        self.tasks: List[BaseSyncTask] = []
        self.pipeline_id = uuid.uuid4()
        self.name = name or f"SyncPipeline-{self.pipeline_id}"

    @classmethod
    def from_tasks(
        cls, tasks: List[BaseSyncTask], name: Optional[str] = None
    ) -> "SyncPipeline":
        pipeline = cls(name)
        for task in tasks:
            pipeline.add_task(task)
        return pipeline

    def add_task(self, task: BaseSyncTask) -> None:
        if not isinstance(task, BaseSyncTask):
            raise TypeError(
                f"Only BaseSyncTask instances can be added. Got {type(task)}"
            )

        sig = inspect.signature(task.execute)
        params = list(sig.parameters.values())
        non_self_params = [p for p in params if p.name != "self"]

        if len(non_self_params) < 1:
            raise TypeError(
                f"Task '{task.task_name}' must define an 'execute(self, input_result: Result)' method "
                "with at least one input parameter."
            )

        param = non_self_params[0]
        if get_origin(param.annotation) is not Result:
            raise TypeError(
                f"Task '{task.task_name}' first argument must be of type Result[T, E]. Found: {param.annotation}"
            )

        self.tasks.append(task)

    def run(
        self,
        input_result: Result[T, E],
        debug: bool = False
    ) -> ExecutionResult[U, E]:
        """
        Run tasks sequentially. Always returns an ExecutionResult whose
        .result is a Result[T, E], and .trace is a Trace if debug=True.
        """
        start = time.perf_counter()
        steps: List[Tuple[str, Result[T, E]]] = []
        result: Result[T, E] = input_result

        if debug:
            steps.append((self.name, result))

        for task in self.tasks:
            name = task.task_name
            try:
                result = task(result)
            except Exception as ex:
                logger.exception(f"[{self.name}] Exception in {name}")
                result = Err(f"Exception in task {name}: {ex}")

            if debug:
                steps.append((name, result))
            # note: we continue even if Err, to record full trace

            if result.is_err() and not debug:
                break

        elapsed = time.perf_counter() - start
        return ExecutionResult(
            result=result,
            trace=Trace(steps=steps) if debug else None,
            execution_time=elapsed
        )

    @staticmethod
    def run_parallel(
        pipelines: List["SyncPipeline[T, E]"],
        inputs: List[Result[T, E]],
        max_workers: int = 4,
        debug: bool = False
    ) -> ExecutionResult[List[Result[U, E]], E]:
        """
        Execute multiple pipelines concurrently. Returns ExecutionResult where
        .result is List[Result[T, E]] (one per pipeline), and .trace is
        Traces(...) if debug=True.
        """
        if len(pipelines) != len(inputs):
            raise AssertionError("Each pipeline needs a corresponding input Result")

        start = time.perf_counter()
        results: List[Result[T, E]] = [None] * len(pipelines)
        pipeline_traces: List[Trace[T, E]] = []

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(p.run, inp, debug): idx
                for idx, (p, inp) in enumerate(zip(pipelines, inputs))
            }

            for fut in as_completed(futures):
                idx = futures[fut]
                pipe = pipelines[idx]
                try:
                    exec_res = fut.result()  # ExecutionResult[T, E]
                except Exception as ex:
                    logger.exception(f"[{pipe.name}] Unhandled exception")
                    results[idx] = Err(f"Exception in pipeline '{pipe.name}': {ex}")
                    if not debug:
                        break
                    exec_res = ExecutionResult(
                        result=results[idx],
                        trace=Trace(steps=[(pipe.name, results[idx])]),
                        execution_time=0.0
                    )

                results[idx] = exec_res.result
                if debug and exec_res.trace is not None:
                    # exec_res.trace is a Trace[T,E]
                    pipeline_traces.append(exec_res.trace)

                if results[idx].is_err() and not debug:
                    break

        elapsed = time.perf_counter() - start
        return ExecutionResult(
            result=results,
            trace=Traces(pipelines=pipeline_traces) if debug else None,
            execution_time=elapsed
        )

    def __str__(self) -> str:
        task_list = "\n  ".join(task.task_name for task in self.tasks)
        return f"{self.name} with {len(self.tasks)} task(s):\n  {task_list}"

    def __repr__(self) -> str:
        return self.__str__()
