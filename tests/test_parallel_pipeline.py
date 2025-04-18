import pytest
from neopipe.result import Ok, Err, Result, PipelineResult
from neopipe.task import FunctionSyncTask, ClassSyncTask
from neopipe.pipeline import SyncPipeline
from typing import Any

# --- Helpers for tests ---

@FunctionSyncTask.decorator()
def to_one(res: Result[None, str]) -> Result[int, str]:
    return Ok(1)

@FunctionSyncTask.decorator()
def to_two(res: Result[None, str]) -> Result[int, str]:
    return Ok(2)

@FunctionSyncTask.decorator()
def fail_task(res: Result[Any, str]) -> Result[Any, str]:
    return Err("task failed")


class AddTask(ClassSyncTask[int, str]):
    def __init__(self, add: int):
        super().__init__()
        self.add = add

    def execute(self, res: Result[int, str]) -> Result[int, str]:
        return Ok(res.unwrap() + self.add) if res.is_ok() else res


# --- Tests ---

def test_parallel_success():
    # pipeline1: None → to_one → AddTask(5) = 1 → 6
    p1 = SyncPipeline.from_tasks([to_one, AddTask(5)], name="P1")
    # pipeline2: None → to_two → AddTask(3) = 2 → 5
    p2 = SyncPipeline.from_tasks([to_two, AddTask(3)], name="P2")

    inputs = [Ok(None), Ok(None)]
    res = SyncPipeline.run_parallel([p1, p2], inputs)

    assert res.is_ok()
    pipeline_results = res.unwrap()

    expected = [
        PipelineResult(name="P1", result=6),
        PipelineResult(name="P2", result=5),
    ]
    assert pipeline_results == expected


def test_parallel_short_circuits_on_error():
    p1 = SyncPipeline.from_tasks([to_one], name="P1")
    p2 = SyncPipeline.from_tasks([fail_task], name="P2")

    inputs = [Ok(None), Ok(None)]
    result = SyncPipeline.run_parallel([p1, p2], inputs)

    assert result.is_err()
    assert result.err() == "task failed"


def test_parallel_input_length_mismatch():
    p1 = SyncPipeline.from_tasks([to_one], name="P1")
    # only one input for two pipelines
    with pytest.raises(AssertionError):
        # we expect run_parallel to return Err, but signature doesn't raise, so:
        _ = SyncPipeline.run_parallel([p1, p1], [Ok(None)])
    # assert res.is_err()
    # assert "corresponding input" in res.err().lower()


def test_parallel_unhandled_exception_in_run():
    # Create a pipeline whose run method throws
    class BadPipeline(SyncPipeline):
        def run(self, *_):
            raise RuntimeError("boom")

    bad = BadPipeline(name="Bad")
    good = SyncPipeline.from_tasks([to_one], name="Good")

    inputs = [Ok(None), Ok(None)]
    result = SyncPipeline.run_parallel([good, bad], inputs)

    assert result.is_err()
    # message should mention the Bad pipeline name
    assert "Bad" in result.err()
    assert "Exception in pipeline" in result.err()
