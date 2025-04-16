import logging
import uuid
from typing import List, Optional, Tuple, TypeVar, Generic, Union, get_origin
from neopipe.result import Result, Ok, Err
from neopipe.task import BaseSyncTask
import inspect

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
    def from_tasks(cls, tasks: List[BaseSyncTask], name: Optional[str] = None) -> "SyncPipeline":
        pipeline = cls(name)
        for task in tasks:
            pipeline.add_task(task)
        return pipeline


    def add_task(self, task: BaseSyncTask) -> None:
        if not isinstance(task, BaseSyncTask):
            raise TypeError(f"Only BaseSyncTask instances can be added. Got {type(task)}")

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
    ) -> Union[Result[U, E], Result[Tuple[Optional[U], List[Tuple[str, Result]]], E]]:
        """
        Run the pipeline sequentially.

        Args:
            input_result (Result): Initial input wrapped in Result.
            debug (bool): If True, returns execution trace as well.

        Returns:
            Result: Final output or failure, with optional trace in debug mode.
        """
        trace: List[Tuple[str, Result]] = []
        result: Result = input_result

        if debug:
            trace.append((self.name, result))

        logger.info(f"[{self.name}] Starting with {len(self.tasks)} task(s)")

        for idx, task in enumerate(self.tasks):
            task_name = task.task_name
            logger.info(f"[{self.name}] Task {idx+1}/{len(self.tasks)} → {task_name}")

            try:
                result = task(result)
            except Exception as e:
                logger.exception(f"[{self.name}] Exception in task {task_name}")
                return Err(f"Exception in task {task_name}: {e}")

            if debug:
                trace.append((task_name, result))

            if result.is_err():
                logger.error(f"[{self.name}] Failed at {task_name}: {result.err()}")
                return Ok((None, trace)) if debug else result

        logger.info(f"[{self.name}] Completed successfully")
        return result if not debug else Ok((result.unwrap(), trace))

    def __str__(self) -> str:
        task_list = "\n  ".join(task.task_name for task in self.tasks)
        return f"{self.name} with {len(self.tasks)} task(s):\n  {task_list}"

    def __repr__(self) -> str:
        return self.__str__()
