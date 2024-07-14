import pytest
from neopipe.result import Result, Ok, Err
from neopipe.task import FunctionTask, ContainerTask, ContainerTaskBase

# Mock function for testing
def success_func(x: int) -> Result[int, str]:
    return Ok(x + 1)

def failure_func(x: int) -> Result[int, str]:
    return Err("Failed to process")

# Mock container task for testing
class MockContainerTask(ContainerTaskBase):
    def __init__(self, factor: int):
        self.factor = factor

    def __call__(self, x: int) -> Result[int, str]:
        if x > 0:
            return Ok(x * self.factor)
        return Err("Invalid input")

def test_function_task_success():
    task = FunctionTask(success_func, retries=3)
    result = task(1)
    assert result.is_ok()
    assert result.unwrap() == 2

def test_function_task_failure():
    task = FunctionTask(failure_func, retries=3)
    result = task(1)
    assert result.is_err()
    assert result.unwrap_err() == "Failed to process"

def test_function_task_retries():
    def flaky_func(x: int) -> Result[int, str]:
        if x == 1:
            raise Exception("Random failure")
        return Ok(x + 1)
    
    task = FunctionTask(flaky_func, retries=3)
    result = task(1)
    assert result.is_err()
    assert "Random failure" in result.unwrap_err()

def test_function_task_eventually_succeeds():
    attempts = 0

    def flaky_func(x: int) -> Result[int, str]:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise Exception("Temporary failure")
        return Ok(x + 1)
    
    task = FunctionTask(flaky_func, retries=3)
    result = task(1)
    assert result.is_ok()
    assert result.unwrap() == 2

def test_container_task_success():
    container = MockContainerTask(factor=2)
    task = ContainerTask(container, retries=3)
    result = task(2)
    assert result.is_ok()
    assert result.unwrap() == 4

def test_container_task_failure():
    container = MockContainerTask(factor=2)
    task = ContainerTask(container, retries=3)
    result = task(0)
    assert result.is_err()
    assert result.unwrap_err() == "Invalid input"

def test_container_task_retries():
    class FlakyContainerTask(ContainerTaskBase):
        def __init__(self):
            self.attempt = 0
        
        def __call__(self, x: int) -> Result[int, str]:
            self.attempt += 1
            if self.attempt < 3:
                raise Exception("Temporary failure")
            return Ok(x * 2)

    container = FlakyContainerTask()
    task = ContainerTask(container, retries=3)
    result = task(2)
    assert result.is_ok()
    assert result.unwrap() == 4

def test_container_task_eventually_succeeds():
    class FlakyContainerTask(ContainerTaskBase):
        def __init__(self):
            self.attempt = 0
        
        def __call__(self, x: int) -> Result[int, str]:
            self.attempt += 1
            if self.attempt < 2:
                raise Exception("Temporary failure")
            return Ok(x * 2)

    container = FlakyContainerTask()
    task = ContainerTask(container, retries=3)
    result = task(2)
    assert result.is_ok()
    assert result.unwrap() == 4
