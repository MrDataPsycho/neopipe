import pytest
from neopipe.result import Result, Ok, Err
from neopipe.task import FunctionTask, ContainerTaskBase, ContainerTask
from neopipe.pipeline import Pipeline
import logging

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

def test_pipeline_with_function_tasks():
    pipeline = Pipeline()

    @pipeline.register(retries=1)
    def add_one(x: int) -> Result[int, str]:
        return Ok(x + 1)

    @pipeline.register(retries=1)
    def multiply_by_two(x: int) -> Result[int, str]:
        return Ok(x * 2)

    result = pipeline.run(1)
    assert result.is_ok()
    assert result.unwrap() == 4

def test_pipeline_with_container_tasks():
    pipeline = Pipeline()
    
    class AddOne(ContainerTaskBase):
        def __call__(self, x: int) -> Result[int, str]:
            return Ok(x + 1)

    class MultiplyByTwo(ContainerTaskBase):
        def __call__(self, x: int) -> Result[int, str]:
            return Ok(x * 2)

    pipeline.register()(AddOne)
    pipeline.register()(MultiplyByTwo)

    result = pipeline.run(1)
    assert result.is_ok()
    assert result.unwrap() == 4

def test_pipeline_mixed_tasks():
    pipeline = Pipeline()

    @pipeline.register(retries=1)
    def add_one(x: int) -> Result[int, str]:
        return Ok(x + 1)

    class MultiplyByTwo(ContainerTaskBase):
        def __call__(self, x: int) -> Result[int, str]:
            return Ok(x * 2)

    pipeline.register()(MultiplyByTwo)

    result = pipeline.run(1)
    assert result.is_ok()
    assert result.unwrap() == 4

def test_pipeline_failure():
    pipeline = Pipeline()

    @pipeline.register(retries=1)
    def fail_task(x: int) -> Result[int, str]:
        return Err("Failed")

    result = pipeline.run(1)
    assert result.is_err()
    assert result.unwrap_err() == "Failed"

def test_pipeline_with_retries():
    pipeline = Pipeline()

    attempt = 0
    @pipeline.register(retries=3)
    def flaky_task(x: int) -> Result[int, str]:
        nonlocal attempt
        attempt += 1
        if attempt < 3:
            raise Exception("Temporary failure")
        return Ok(x + 1)

    result = pipeline.run(1)
    assert result.is_ok()
    assert result.unwrap() == 2

def test_append_task():
    pipeline = Pipeline()
    pipeline.append_task(FunctionTask(success_func, retries=1))
    pipeline.append_task(ContainerTask(MockContainerTask(factor=2), retries=1))

    result = pipeline.run(1)
    assert result.is_ok()
    assert result.unwrap() == 4

def test_invalid_append_task():
    pipeline = Pipeline()
    with pytest.raises(TypeError):
        pipeline.append_task("invalid task")

def test_invalid_register_task():
    pipeline = Pipeline()
    with pytest.raises(TypeError):
        @pipeline.register()
        class InvalidTask:
            pass

def test_show_execution_plan(capsys):
    pipeline = Pipeline()

    @pipeline.register(retries=1)
    def add_one(x: int) -> Result[int, str]:
        return Ok(x + 1)

    class MultiplyByTwo(ContainerTaskBase):
        def __call__(self, x: int) -> Result[int, str]:
            return Ok(x * 2)

    pipeline.register()(MultiplyByTwo)
    pipeline.show_execution_plan()
    captured = capsys.readouterr()
    assert "add_one" in captured.out
    assert "MultiplyByTwo" in captured.out

def test_pipeline_run_with_progress(caplog):
    pipeline = Pipeline()

    @pipeline.register(retries=1)
    def add_one(x: int) -> Result[int, str]:
        return Ok(x + 1)

    @pipeline.register(retries=1)
    def multiply_by_two(x: int) -> Result[int, str]:
        return Ok(x * 2)

    with caplog.at_level(logging.INFO):
        result = pipeline.run(1, show_progress=True)
        assert "1/2 is complete" in caplog.text
        assert "2/2 is complete" in caplog.text

    assert result.is_ok()
    assert result.unwrap() == 4
