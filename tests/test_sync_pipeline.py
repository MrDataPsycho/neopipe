import pytest
from typing import Any
from neopipe.result import Ok, Err, Result
from neopipe.task import ClassSyncTask, FunctionSyncTask
from neopipe.pipeline import SyncPipeline


# ------------------------------
# Test for missing parameter in execute
# ------------------------------

class BadTaskNoParam(ClassSyncTask):
    def execute(self) -> Result[int, str]:  # ❌ No input param
        return Ok(42)

def test_missing_execute_param_raises():
    pipeline = SyncPipeline()
    with pytest.raises(TypeError, match="must define an 'execute"):
        pipeline.add_task(BadTaskNoParam())


# ------------------------------
# Test for wrong parameter type in execute
# ------------------------------

class BadTaskWrongType(ClassSyncTask):
    def execute(self, x: int) -> Result[int, str]:  # ❌ Not a Result param
        return Ok(x + 1)

def test_wrong_execute_param_type_raises():
    pipeline = SyncPipeline()
    with pytest.raises(TypeError, match="first argument must be of type Result"):
        pipeline.add_task(BadTaskWrongType())


# ------------------------------
# Test for type mismatch between tasks
# ------------------------------

@FunctionSyncTask.decorator()
def produce_string(res: Result[Any, str]) -> Result[str, str]:
    return Ok("hello")

@FunctionSyncTask.decorator()
def expects_int(res: Result[int, str]) -> Result[int, str]:  # ❌ Will mismatch
    return Ok(res.unwrap() + 1)


# ------------------------------
# Happy path: all types correct
# ------------------------------

@FunctionSyncTask.decorator()
def start_with_number(res: Result[Any, str]) -> Result[int, str]:
    return Ok(10)

@FunctionSyncTask.decorator()
def increment(res: Result[int, str]) -> Result[int, str]:
    return Ok(res.unwrap() + 1)

class MultiplyTask(ClassSyncTask[int, str]):
    def __init__(self, multiplier: int):
        super().__init__()
        self.multiplier = multiplier

    def execute(self, res: Result[int, str]) -> Result[int, str]:
        return Ok(res.unwrap() * self.multiplier)

def test_pipeline_valid_execution():
    pipeline = SyncPipeline.from_tasks([start_with_number, increment, MultiplyTask(3)])
    result = pipeline.run(Ok(None))
    assert result == Ok(33)
