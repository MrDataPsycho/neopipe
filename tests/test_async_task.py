import pytest
import asyncio
from neopipe.result import Result, Ok, Err
from neopipe.task import FunctionAsyncTask, ClassAsyncTask


# ----------------------------
# FunctionAsyncTask Tests
# ----------------------------

@FunctionAsyncTask.decorator(retries=2)
async def multiply_by_two(x: int) -> Result[int, str]:
    await asyncio.sleep(0.01)
    return Ok(x * 2)

@FunctionAsyncTask.decorator(retries=2)
async def always_err(_: int) -> Result[int, str]:
    return Err("always fails")

@FunctionAsyncTask.decorator(retries=2)
async def raises_exception(_: int) -> Result[int, str]:
    raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_async_function_success():
    result = await multiply_by_two(5)
    assert result == Ok(10)


@pytest.mark.asyncio
async def test_async_function_returns_err():
    result = await always_err(1)
    assert result.is_err()
    assert result.err() == "always fails"


@pytest.mark.asyncio
async def test_async_function_exception_retry():
    result = await raises_exception(1)
    assert result.is_err()
    assert "failed after 2 retries" in result.err().lower()


# ----------------------------
# ClassAsyncTask Tests
# ----------------------------

class AddTenTask(ClassAsyncTask[int, str]):
    def __init__(self, value: int, fail_first: bool = False):
        super().__init__(retries=2)
        self.value = value
        self.fail_first = fail_first
        self.attempts = 0

    async def execute(self) -> Result[int, str]:
        await asyncio.sleep(0.01)
        self.attempts += 1
        if self.fail_first and self.attempts == 1:
            raise ValueError("fail once")
        return Ok(self.value + 10)


@pytest.mark.asyncio
async def test_class_async_task_success():
    task = AddTenTask(15)
    result = await task()
    assert result == Ok(25)


@pytest.mark.asyncio
async def test_class_async_task_retries_on_exception():
    task = AddTenTask(5, fail_first=True)
    result = await task()
    assert result == Ok(15)
    assert task.attempts == 2


class ExplodingTask(ClassAsyncTask[int, str]):
    async def execute(self) -> Result[int, str]:
        raise RuntimeError("always boom")


@pytest.mark.asyncio
async def test_class_async_task_permanent_failure():
    task = ExplodingTask(retries=3)
    result = await task()
    assert result.is_err()
    assert "failed after 3 retries" in result.err()


# ----------------------------
# Metadata Tests
# ----------------------------

@pytest.mark.asyncio
async def test_async_task_ids_are_unique():
    t1 = AddTenTask(1)
    t2 = AddTenTask(2)
    assert t1.task_id != t2.task_id

    f1 = FunctionAsyncTask(lambda x: Ok(x))
    f2 = FunctionAsyncTask(lambda x: Ok(x))
    assert f1.task_id != f2.task_id
