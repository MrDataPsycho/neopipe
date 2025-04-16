from neopipe.result import Err, Ok, Result
from neopipe.task import ClassSyncTask, FunctionSyncTask

# -----------------------------
# FunctionSyncTask definitions
# -----------------------------


@FunctionSyncTask.decorator(retries=2)
def add_10(result: Result[int, str]) -> Result[int, str]:
    if result.is_ok():
        return Ok(result.unwrap() + 10)
    return result


@FunctionSyncTask.decorator(retries=2)
def fail_on_zero(result: Result[int, str]) -> Result[int, str]:
    if result.is_ok() and result.unwrap() == 0:
        return Err("Cannot be zero")
    return result


# -----------------------------
# ClassSyncTask definitions
# -----------------------------


class MultiplyTask(ClassSyncTask[int, str]):
    def __init__(self, multiplier: int):
        super().__init__()
        self.multiplier = multiplier

    def execute(self, result: Result[int, str]) -> Result[int, str]:
        if result.is_ok():
            return Ok(result.unwrap() * self.multiplier)
        return result


class AlwaysFailTask(ClassSyncTask[int, str]):
    def execute(self, result: Result[int, str]) -> Result[int, str]:
        return Err("Always fails")


# -----------------------------
# Tests for FunctionSyncTask
# -----------------------------


def test_function_sync_task_success():
    input_result = Ok(5)
    output = add_10(input_result)
    assert output == Ok(15)


def test_function_sync_task_propagates_err():
    err = Err("bad input")
    output = add_10(err)
    assert output == err


def test_function_sync_task_fails_on_zero():
    result = fail_on_zero(Ok(0))
    assert result.is_err()
    assert result.err() == "Cannot be zero"


# -----------------------------
# Tests for ClassSyncTask
# -----------------------------


def test_class_sync_task_success():
    task = MultiplyTask(multiplier=3)
    output = task(Ok(7))
    assert output == Ok(21)


def test_class_sync_task_propagates_err():
    task = MultiplyTask(2)
    output = task(Err("upstream error"))
    assert output == Err("upstream error")


def test_class_sync_task_always_fails():
    task = AlwaysFailTask()
    result = task(Ok(123))
    assert result.is_err()
    assert result.err() == "Always fails"


# -----------------------------
# Task Name Checks
# -----------------------------


def test_function_task_name():
    assert add_10.task_name == "add_10"


def test_class_task_name():
    task = MultiplyTask(2)
    assert task.task_name == "MultiplyTask"
