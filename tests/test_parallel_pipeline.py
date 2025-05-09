import pytest
from typing import Any
from neopipe.result import Ok, Err, Result, ExecutionResult
from neopipe.task import FunctionSyncTask, ClassSyncTask
from neopipe.pipeline import SyncPipeline

# --- Task definitions for tests ---

@FunctionSyncTask.decorator()
def to_one(res: Result[None, str]) -> Result[int, str]:
    """Always returns Ok(1)."""
    return Ok(1)

@FunctionSyncTask.decorator()
def to_two(res: Result[None, str]) -> Result[int, str]:
    """Always returns Ok(2)."""
    return Ok(2)

@FunctionSyncTask.decorator()
def fail_task(res: Result[Any, str]) -> Result[Any, str]:
    """Always returns Err('task failed')."""
    return Err("task failed")


class AddTask(ClassSyncTask[int, str]):
    """Adds a fixed integer to the input value."""
    def __init__(self, add: int):
        super().__init__()
        self.add = add

    def execute(self, res: Result[int, str]) -> Result[int, str]:
        return Ok(res.unwrap() + self.add) if res.is_ok() else res


# --- Parallel Execution Tests ---

def test_run_parallel_success():
    """
    run_parallel should return an ExecutionResult whose .result is
    a list of Ok values, in the same order as the pipelines.
    """
    p1 = SyncPipeline.from_tasks([to_one, AddTask(5)], name="P1")
    p2 = SyncPipeline.from_tasks([to_two, AddTask(3)], name="P2")
    inputs = [Ok(None), Ok(None)]

    exec_res = SyncPipeline.run_parallel([p1, p2], inputs, debug=False)
    assert isinstance(exec_res, ExecutionResult)

    results = exec_res.result
    assert results == [Ok(6), Ok(5)]


def test_run_parallel_short_circuits_on_error():
    """
    run_parallel without debug should stop at first Err,
    but still return an ExecutionResult containing that Err.
    """
    p1 = SyncPipeline.from_tasks([to_one], name="P1")
    p2 = SyncPipeline.from_tasks([fail_task], name="P2")
    inputs = [Ok(None), Ok(None)]

    exec_res = SyncPipeline.run_parallel([p1, p2], inputs, debug=False)
    assert isinstance(exec_res, ExecutionResult)

    results = exec_res.result
    # first pipeline succeeds, second fails
    assert results[0] == Ok(1)
    assert results[1] == Err("task failed")


def test_run_parallel_input_length_mismatch():
    """
    run_parallel should raise an AssertionError if the number of inputs
    does not match the number of pipelines.
    """
    p = SyncPipeline.from_tasks([to_one], name="P1")
    with pytest.raises(AssertionError):
        SyncPipeline.run_parallel([p, p], [Ok(None)])


def test_run_parallel_unhandled_exception():
    """
    If a pipeline.run() raises an unexpected exception, run_parallel should
    catch it and place an Err in the corresponding slot of .result.
    """
    class BadPipeline(SyncPipeline):
        def run(self, *args, **kwargs):
            raise RuntimeError("boom")

    bad = BadPipeline(name="Bad")
    good = SyncPipeline.from_tasks([to_one], name="Good")
    inputs = [Ok(None), Ok(None)]

    exec_res = SyncPipeline.run_parallel([good, bad], inputs, debug=False)
    assert isinstance(exec_res, ExecutionResult)

    results = exec_res.result
    # good pipeline still Ok
    assert results[0] == Ok(1)
    # bad pipeline captured the exception
    assert results[1].is_err()
    assert "boom" in results[1].err()
