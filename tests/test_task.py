import pytest
from typing import Any
from neopipe.result import Result, Ok, Err
from neopipe.task import FunctionSyncTask, ClassSyncTask
import asyncio


# ------------------------
# FunctionSyncTask Tests
# ------------------------

@FunctionSyncTask.decorator(retries=2)
def add_one(x: int) -> Result[int, str]:
    return Ok(x + 1)

@FunctionSyncTask.decorator(retries=2)
def always_fails(_: Any) -> Result[int, str]:
    return Err("always fails")

@FunctionSyncTask.decorator(retries=2)
def raises_exception(_: Any) -> Result[int, str]:
    raise ValueError("unexpected error")


def test_function_sync_task_success():
    result = add_one(4)
    assert result == Ok(5)


def test_function_sync_task_failure_err():
    result = always_fails("anything")
    assert result.is_err()
    assert result.err() == "always fails"


def test_function_sync_task_failure_exception():
    result = raises_exception("input")
    assert result.is_err()
    assert "failed after 2 retries" in result.err()


# ------------------------
# ClassSyncTask Tests
# ------------------------

class AddTenTask(ClassSyncTask[int, str]):
    def __init__(self, val: int, fail=False):
        super().__init__(retries=3)
        self.val = val
        self.fail = fail

    def execute(self) -> Result[int, str]:
        if self.fail:
            raise RuntimeError("Intentional failure")
        return Ok(self.val + 10)


def test_class_sync_task_success():
    task = AddTenTask(5)
    result = task()
    assert result == Ok(15)


def test_class_sync_task_exception_retry():
    task = AddTenTask(1, fail=True)
    result = task()
    assert result.is_err()
    assert "failed after" in result.err()


# ------------------------
# Task ID Check
# ------------------------

def test_task_has_unique_id():
    t1 = AddTenTask(1)
    t2 = AddTenTask(2)
    assert t1.task_id != t2.task_id

    f1 = FunctionSyncTask(lambda x: Ok(x * 2))
    f2 = FunctionSyncTask(lambda x: Ok(x * 2))
    assert f1.task_id != f2.task_id


# # ----------------------------
# # FunctionAsyncTask Tests
# # ----------------------------

# @FunctionAsyncTask.decorator(retries=2)
# async def multiply_by_two(x: int) -> Result[int, str]:
#     await asyncio.sleep(0.01)
#     return Ok(x * 2)


# @FunctionAsyncTask.decorator(retries=2)
# async def always_err(_: int) -> Result[int, str]:
#     return Err("always fails")

# @FunctionAsyncTask.decorator(retries=2)
# async def raises_exception(_: int) -> Result[int, str]:
#     raise RuntimeError("boom")


# @pytest.mark.asyncio
# async def test_async_function_success():
#     result = await multiply_by_two(5)
#     assert result == Ok(10)