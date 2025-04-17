import pytest
from neopipe.result import Ok, Err, Result
from neopipe.task import FunctionAsyncTask, ClassAsyncTask
from neopipe.async_pipeline import AsyncPipeline


# --------------
# Test task definitions
# --------------

@FunctionAsyncTask.decorator(retries=2)
async def add_one(res: Result[int, str]) -> Result[int, str]:
    if res.is_ok():
        return Ok(res.unwrap() + 1)
    return res

@FunctionAsyncTask.decorator(retries=2)
async def multiply_two(res: Result[int, str]) -> Result[int, str]:
    if res.is_ok():
        return Ok(res.unwrap() * 2)
    return res

@FunctionAsyncTask.decorator(retries=1)
async def fail_task(res: Result[int, str]) -> Result[int, str]:
    return Err("failure")


class ValidClassTask(ClassAsyncTask[int, str]):
    async def execute(self, res: Result[int, str]) -> Result[int, str]:
        if res.is_ok():
            return Ok(res.unwrap() + 10)
        return res

class NoParamTask(ClassAsyncTask[int, str]):
    async def execute(self) -> Result[int, str]:  # Missing the input parameter
        return Ok(0)

class WrongTypeTask(ClassAsyncTask[int, str]):
    async def execute(self, x: int) -> Result[int, str]:  # Wrong annotation
        return Ok(x)

class ExceptionTask(ClassAsyncTask[int, str]):
    async def execute(self, res: Result[int, str]) -> Result[int, str]:
        raise RuntimeError("boom")


# ----------------------
# Validation Tests
# ----------------------

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


# ----------------------
# Input length mismatch
# ----------------------

@pytest.mark.asyncio
async def test_run_input_length_mismatch():
    pipeline = AsyncPipeline.from_tasks([add_one, multiply_two])
    res = await pipeline.run([Ok(1)])
    assert res.is_err()
    assert "Number of inputs must match" in res.err()


# ----------------------
# Successful concurrent execution
# ----------------------

@pytest.mark.asyncio
async def test_run_success():
    pipeline = AsyncPipeline.from_tasks([add_one, multiply_two])
    res = await pipeline.run([Ok(1), Ok(2)])
    assert res == Ok([2, 4])


# ----------------------
# Error short-circuit
# ----------------------

@pytest.mark.asyncio
async def test_run_short_circuit_on_err():
    pipeline = AsyncPipeline.from_tasks([add_one, fail_task, multiply_two])
    res = await pipeline.run([Ok(1), Ok(2), Ok(3)])
    assert res.is_err()
    assert res.err() == "failure"


# ----------------------
# Debug mode captures trace
# ----------------------

@pytest.mark.asyncio
async def test_run_debug_trace_success():
    pipeline = AsyncPipeline.from_tasks([add_one, multiply_two])
    res = await pipeline.run([Ok(3), Ok(4)], debug=True)
    assert res.is_ok()
    outputs, trace = res.unwrap()
    assert outputs == [4, 8]
    assert isinstance(trace, list)
    assert trace[0][0] == add_one.task_name
    assert trace[0][1] == Ok(4)
    assert trace[1][0] == multiply_two.task_name
    assert trace[1][1] == Ok(8)

@pytest.mark.asyncio
async def test_run_debug_trace_failure():
    pipeline = AsyncPipeline.from_tasks([add_one, fail_task, multiply_two])
    res = await pipeline.run([Ok(5), Ok(6), Ok(7)], debug=True)
    assert res.is_ok()  # Err wrapped in Ok((None, trace))
    final, trace = res.unwrap()
    assert final is None
    # trace should include at least two entries
    assert len(trace) == 2
    assert trace[0][0] == add_one.task_name
    assert trace[1][0] == fail_task.task_name
    assert trace[1][1] == Err("failure")


# ----------------------
# Unhandled exception in gather
# ----------------------

@pytest.mark.asyncio
async def test_run_unhandled_exception():
    pipeline = AsyncPipeline.from_tasks([add_one, ExceptionTask()])
    res = await pipeline.run([Ok(1), Ok(2)])
    assert res.is_err()
    assert "boom" in res.err()
