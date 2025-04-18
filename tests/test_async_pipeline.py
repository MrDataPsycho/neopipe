import pytest
from neopipe.result import Result, Ok, Err
from neopipe.task import FunctionAsyncTask, ClassAsyncTask
from neopipe.async_pipeline import AsyncPipeline
from typing import Any

# ----------------------------
# Task Definitions
# ----------------------------

@FunctionAsyncTask.decorator(retries=1)
async def add_one(res: Result[int, str]) -> Result[int, str]:
    if res.is_ok():
        return Ok(res.unwrap() + 1)
    return res

@FunctionAsyncTask.decorator(retries=1)
async def multiply_two(res: Result[int, str]) -> Result[int, str]:
    if res.is_ok():
        return Ok(res.unwrap() * 2)
    return res

@FunctionAsyncTask.decorator(retries=1)
async def fail_task(res: Result[int, str]) -> Result[int, str]:
    return Err("error occurred")

class ValidClassTask(ClassAsyncTask[int, str]):
    async def execute(self, res: Result[int, str]) -> Result[int, str]:
        if res.is_ok():
            return Ok(res.unwrap() + 10)
        return res

class NoParamTask(ClassAsyncTask[int, str]):
    async def execute(self) -> Result[int, str]:  # Missing input parameter
        return Ok(0)

class WrongTypeTask(ClassAsyncTask[int, str]):
    async def execute(self, x: int) -> Result[int, str]:  # Wrong annotation
        return Ok(x)

# ----------------------------
# Validation Tests
# ----------------------------

def test_add_task_invalid_type_raises():
    pipeline = AsyncPipeline()
    with pytest.raises(TypeError):
        pipeline.add_task(object())


def test_add_task_no_param_raises():
    pipeline = AsyncPipeline()
    with pytest.raises(TypeError):
        pipeline.add_task(NoParamTask())


def test_add_task_wrong_type_annotation_raises():
    pipeline = AsyncPipeline()
    with pytest.raises(TypeError):
        pipeline.add_task(WrongTypeTask())

# ----------------------------
# run: input length mismatch
# ----------------------------

@pytest.mark.asyncio
async def test_run_input_length_mismatch():
    pipeline = AsyncPipeline.from_tasks([add_one, multiply_two])
    res = await pipeline.run([Ok(1)])
    assert res.is_err()
    assert "Number of inputs must match" in res.err()

# ----------------------------
# run: successful concurrent execution
# ----------------------------

@pytest.mark.asyncio
async def test_run_success():
    pipeline = AsyncPipeline.from_tasks([add_one, multiply_two])
    res = await pipeline.run([Ok(1), Ok(2)])
    assert res == Ok([2, 4])

# ----------------------------
# run: short-circuit on error
# ----------------------------

@pytest.mark.asyncio
async def test_run_short_circuit_on_error():
    pipeline = AsyncPipeline.from_tasks([add_one, fail_task, multiply_two])
    res = await pipeline.run([Ok(1), Ok(2), Ok(3)])
    assert res.is_err()
    assert res.err() == "error occurred"

# ----------------------------
# run: debug trace
# ----------------------------

@pytest.mark.asyncio
async def test_run_debug_trace_success():
    pipeline = AsyncPipeline.from_tasks([add_one, multiply_two])
    res = await pipeline.run([Ok(5), Ok(3)], debug=True)
    assert res.is_ok()
    outputs, trace = res.unwrap()
    assert outputs == [6, 6]
    assert len(trace) == 2
    assert trace[0][0] == add_one.task_name
    assert trace[0][1] == Ok(6)
    assert trace[1][0] == multiply_two.task_name
    assert trace[1][1] == Ok(6)

@pytest.mark.asyncio
async def test_run_debug_trace_failure():
    pipeline = AsyncPipeline.from_tasks([add_one, fail_task, multiply_two])
    res = await pipeline.run([Ok(2), Ok(0), Ok(0)], debug=True)
    assert res.is_ok()
    final, trace = res.unwrap()
    assert final is None
    assert len(trace) == 2
    assert trace[1][1] == Err("error occurred")

# ----------------------------
# run_sequence: sequential execution
# ----------------------------

@pytest.mark.asyncio
async def test_run_sequence_success():
    pipeline = AsyncPipeline.from_tasks([add_one, multiply_two])
    res = await pipeline.run_sequence(Ok(2))
    assert res == Ok(6)

@pytest.mark.asyncio
async def test_run_sequence_error_short_circuit():
    pipeline = AsyncPipeline.from_tasks([add_one, fail_task, multiply_two])
    res = await pipeline.run_sequence(Ok(3))
    assert res.is_err()
    assert res.err() == "error occurred"

@pytest.mark.asyncio
async def test_run_sequence_debug_trace():
    pipeline = AsyncPipeline.from_tasks([add_one, multiply_two])
    res = await pipeline.run_sequence(Ok(4), debug=True)
    assert res.is_ok()
    final, trace = res.unwrap()
    assert final == 10
    assert len(trace) == 2

# ----------------------------
# run_parallel: combine pipelines
# ----------------------------

@pytest.mark.asyncio
async def test_run_parallel_success():
    p1 = AsyncPipeline.from_tasks([add_one, multiply_two])
    p2 = AsyncPipeline.from_tasks([multiply_two, add_one])
    inputs = [Ok(1), Ok(2)]
    res = await AsyncPipeline.run_parallel([p1, p2], inputs)
    assert res == Ok([[2, 4], [4, 5]])

@pytest.mark.asyncio
async def test_run_parallel_input_mismatch():
    p1 = AsyncPipeline.from_tasks([add_one])
    with pytest.raises(AssertionError):
        # expecting Err, but method returns Err not raises—adjust accordingly
        res = await AsyncPipeline.run_parallel([p1, p1], [Ok(1)])
        assert res.is_err()

@pytest.mark.asyncio
async def test_run_parallel_debug_trace_and_short_circuit():
    p1 = AsyncPipeline.from_tasks([add_one])
    p2 = AsyncPipeline.from_tasks([fail_task])
    inputs = [Ok(3), Ok(4)]
    res = await AsyncPipeline.run_parallel([p1, p2], inputs, debug=True)
    assert res.is_ok()
    outputs, trace = res.unwrap()
    assert outputs[0] == 4
    assert outputs[1] is None
    assert any(entry[0] == fail_task.task_name and entry[1] == Err("error occurred") for entry in trace)

@pytest.mark.asyncio
async def test_run_parallel_unhandled_exception():
    # pipeline whose run_sequence raises
    class BadPipeline(AsyncPipeline):
        async def run_sequence(self, inp, debug=False):
            raise RuntimeError("boom")
    bad = BadPipeline.from_tasks([add_one])
    res = await AsyncPipeline.run_parallel([bad], [Ok(1)])
    assert res.is_err()
    assert "boom" in res.err()
