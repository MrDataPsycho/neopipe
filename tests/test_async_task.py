import pytest

from neopipe.result import Err, Ok, Result
from neopipe.task import ClassAsyncTask, FunctionAsyncTask

# -----------------------------
# FunctionAsyncTask definitions
# -----------------------------


@FunctionAsyncTask.decorator(retries=2)
async def append_exclaim(result: Result[str, str]) -> Result[str, str]:
    if result.is_ok():
        return Ok(result.unwrap() + "!")
    return result


@FunctionAsyncTask.decorator(retries=2)
async def fail_if_empty(result: Result[str, str]) -> Result[str, str]:
    if result.is_ok() and result.unwrap().strip() == "":
        return Err("Input is empty")
    return result


@FunctionAsyncTask.decorator(retries=2)
async def raise_exception(result: Result[str, str]) -> Result[str, str]:
    raise RuntimeError("Something went wrong")


# -----------------------------
# ClassAsyncTask definitions
# -----------------------------


class ToUpperTask(ClassAsyncTask[str, str]):
    async def execute(self, result: Result[str, str]) -> Result[str, str]:
        if result.is_ok():
            return Ok(result.unwrap().upper())
        return result


class AlwaysFailAsyncTask(ClassAsyncTask[str, str]):
    async def execute(self, result: Result[str, str]) -> Result[str, str]:
        return Err("Always fails")


# -----------------------------
# Async Function Task Tests
# -----------------------------


@pytest.mark.asyncio
async def test_function_async_success():
    res = await append_exclaim(Ok("hello"))
    assert res == Ok("hello!")


@pytest.mark.asyncio
async def test_function_async_err_propagation():
    res = await append_exclaim(Err("bad input"))
    assert res == Err("bad input")


@pytest.mark.asyncio
async def test_function_async_validation_failure():
    res = await fail_if_empty(Ok("  "))
    assert res.is_err()
    assert res.err() == "Input is empty"


@pytest.mark.asyncio
async def test_function_async_exception_retry():
    res = await raise_exception(Ok("boom"))
    assert res.is_err()
    assert "failed after 2 retries" in res.err().lower()


# -----------------------------
# Async Class Task Tests
# -----------------------------


@pytest.mark.asyncio
async def test_class_async_task_success():
    task = ToUpperTask()
    res = await task(Ok("test"))
    assert res == Ok("TEST")


@pytest.mark.asyncio
async def test_class_async_task_err_passthrough():
    task = ToUpperTask()
    res = await task(Err("bad"))
    assert res == Err("bad")


@pytest.mark.asyncio
async def test_class_async_task_always_fails():
    task = AlwaysFailAsyncTask()
    res = await task(Ok("something"))
    assert res.is_err()
    assert res.err() == "Always fails"


# -----------------------------
# Task Name Checks
# -----------------------------


def test_function_async_task_name():
    assert append_exclaim.task_name == "append_exclaim"


def test_class_async_task_name():
    task = ToUpperTask()
    assert task.task_name == "ToUpperTask"
