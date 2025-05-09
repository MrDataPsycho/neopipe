import pytest
import asyncio
from neopipe.result import Ok, Err, Result, Trace, ExecutionResult
from neopipe.task import FunctionAsyncTask, ClassAsyncTask
from neopipe.async_pipeline import AsyncPipeline

# -- Task definitions for async tests --

@FunctionAsyncTask.decorator()
async def add_one_async(res: Result[int, str]) -> Result[int, str]:
    """Increment an Ok value by 1, propagate Err."""
    if res.is_ok():
        return Ok(res.unwrap() + 1)
    return res

@FunctionAsyncTask.decorator()
async def fail_async(res: Result[int, str]) -> Result[int, str]:
    """Always return an Err."""
    return Err("failure occurred")

class MultiplyAsync(ClassAsyncTask[int, str]):
    """Multiply the Ok value by a given factor asynchronously."""
    def __init__(self, multiplier: int):
        super().__init__()
        self.multiplier = multiplier

    async def execute(self, res: Result[int, str]) -> Result[int, str]:
        if res.is_ok():
            return Ok(res.unwrap() * self.multiplier)
        return res

# ----------------------------
# tests/test_async_pipeline.py
# ----------------------------

@pytest.mark.asyncio
async def test_run_concurrent_success():
    """
    AsyncPipeline.run should execute tasks concurrently, returning
    an ExecutionResult with .result as a list of Result values,
    and no trace when debug=False.
    """
    pipeline = AsyncPipeline.from_tasks([add_one_async, add_one_async], name="IncAsync")
    inputs = [Ok(1), Ok(2)]
    exec_res = await pipeline.run(inputs, debug=False)

    assert isinstance(exec_res, ExecutionResult)
    # .result is a list of Result[int, str]
    assert isinstance(exec_res.result, list)
    assert exec_res.result == [Ok(2), Ok(3)]
    # No trace when debug=False
    assert exec_res.trace is None

@pytest.mark.asyncio
async def test_run_concurrent_debug():
    """
    AsyncPipeline.run with debug=True should produce both the list of Results
    and a Trace object with one entry per task.
    """
    pipeline = AsyncPipeline.from_tasks([add_one_async, add_one_async], name="IncAsync")
    inputs = [Ok(5), Ok(6)]
    exec_res = await pipeline.run(inputs, debug=True)

    assert isinstance(exec_res, ExecutionResult)
    assert exec_res.result == [Ok(6), Ok(7)]
    # Trace should record each task's name and Result
    assert isinstance(exec_res.trace, Trace)
    steps = exec_res.trace.steps
    assert steps == [("add_one_async", Ok(6)), ("add_one_async", Ok(7))]

@pytest.mark.asyncio
async def test_run_sequence_success():
    """
    AsyncPipeline.run_sequence should chain tasks in sequence,
    returning ExecutionResult.result as a single Result,
    and no trace when debug=False.
    """
    pipeline = AsyncPipeline.from_tasks([add_one_async, add_one_async], name="SeqAsync")
    exec_res = await pipeline.run_sequence(Ok(3), debug=False)

    assert isinstance(exec_res, ExecutionResult)
    assert isinstance(exec_res.result, Result)
    assert exec_res.result == Ok(5)
    assert exec_res.trace is None

@pytest.mark.asyncio
async def test_run_sequence_debug_error():
    """
    AsyncPipeline.run_sequence with debug=True should include all steps
    even after a failure, recording both successes and the Err.
    """
    pipeline = AsyncPipeline.from_tasks(
        [add_one_async, fail_async, add_one_async],
        name="SeqAsyncErr"
    )
    exec_res = await pipeline.run_sequence(Ok(2), debug=True)

    assert isinstance(exec_res, ExecutionResult)
    # Final result is Err
    assert exec_res.result == Err("failure occurred")
    # Trace should record each step up to the failure
    assert isinstance(exec_res.trace, Trace)
    steps = exec_res.trace.steps
    assert steps[0] == ("add_one_async", Ok(3))
    assert steps[1] == ("fail_async", Err("failure occurred"))

@pytest.mark.asyncio
async def test_run_parallel_success():
    """
    AsyncPipeline.run_parallel should run multiple pipelines concurrently,
    returning an ExecutionResult with .result as a list of Result values.
    """
    p1 = AsyncPipeline.from_tasks([add_one_async], name="P1")
    p2 = AsyncPipeline.from_tasks([add_one_async, MultiplyAsync(3)], name="P2")
    inputs = [Ok(4), Ok(5)]

    exec_res = await AsyncPipeline.run_parallel([p1, p2], inputs, debug=False)

    assert isinstance(exec_res, ExecutionResult)
    # .result is a list of Result[int, str]
    assert exec_res.result == [Ok(5), Ok(18)]
    assert exec_res.trace is None

@pytest.mark.asyncio
async def test_run_parallel_input_length_mismatch():
    """
    AsyncPipeline.run_parallel should raise AssertionError if the number of inputs
    does not match the number of pipelines.
    """
    p = AsyncPipeline.from_tasks([add_one_async], name="Single")
    with pytest.raises(AssertionError):
        await AsyncPipeline.run_parallel([p, p], [Ok(1)])

@pytest.mark.asyncio
async def test_run_parallel_unhandled_exception():
    """
    If a pipeline.run_sequence raises an exception, run_parallel should catch it
    and include an Err in the results list, without crashing.
    """
    class BadAsyncPipeline(AsyncPipeline[int, str]):
        async def run_sequence(self, *args, **kwargs):
            raise RuntimeError("boom")

    bad = BadAsyncPipeline(name="Bad")
    good = AsyncPipeline.from_tasks([add_one_async], name="Good")
    inputs = [Ok(1), Ok(2)]

    exec_res = await AsyncPipeline.run_parallel([good, bad], inputs, debug=False)

    assert isinstance(exec_res, ExecutionResult)
    # Good pipeline result
    assert exec_res.result[0] == Ok(2)
    # Bad pipeline captured exception as Err
    assert exec_res.result[1].is_err()
    assert "boom" in exec_res.result[1].err()
