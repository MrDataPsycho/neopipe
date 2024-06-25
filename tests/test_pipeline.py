import pytest
from neopipe.pipeline import Pipeline
from neopipe.task import Task
from neopipe.result import Result, Ok, Err

def dummy_task_ok(data):
    return Ok(data + 1)

def dummy_task_err(data):
    return Err("Task failed")

def dummy_task_with_types(data: int) -> Result[int, str]:
    return Ok(data + 1)

def test_pipeline_creation():
    pipeline = Pipeline()
    assert isinstance(pipeline, Pipeline)
    assert len(pipeline.registry) == 0

def test_pipeline_from_tasks():
    task1 = Task(dummy_task_ok)
    task2 = Task(dummy_task_ok)
    tasks = [task1, task2]
    pipeline = Pipeline.from_tasks(tasks)
    assert len(pipeline.registry) == 2

def test_register_function():
    pipeline = Pipeline()
    @pipeline.register(retries=2)
    def add_one(data):
        return Ok(data + 1)

    assert len(pipeline.registry) == 1

def test_append_function_to_registry():
    pipeline = Pipeline()
    pipeline.append_function_to_registry(dummy_task_ok, retries=2)
    assert len(pipeline.registry) == 1

def test_append_task_to_registry():
    pipeline = Pipeline()
    task = Task(dummy_task_ok, retries=2)
    pipeline.append_task_to_registry(task)
    assert len(pipeline.registry) == 1

def test_append_task_to_registry_invalid():
    pipeline = Pipeline()
    with pytest.raises(ValueError, match="task must be an instance of Task"):
        pipeline.append_task_to_registry("not_a_task")


def test_run_pipeline_ok():
    pipeline = Pipeline()
    pipeline.append_function_to_registry(dummy_task_ok)
    result = pipeline.run(initial_value=1)
    assert result.is_ok()
    assert result.unwrap() == 2

def test_run_pipeline_err():
    pipeline = Pipeline()
    pipeline.append_function_to_registry(dummy_task_err)
    result = pipeline.run(initial_value=1)
    assert result.is_err()
    assert result.unwrap_err() == "Task failed"


def test_pipeline_str():
    pipeline = Pipeline()
    pipeline.append_function_to_registry(dummy_task_ok)
    assert str(pipeline) == "Pipeline with 1 tasks:\n  Task(dummy_task_ok, retries=1)"

def test_pipeline_repr():
    pipeline = Pipeline()
    pipeline.append_function_to_registry(dummy_task_ok)
    assert repr(pipeline) == "Pipeline with 1 tasks:\n  Task(dummy_task_ok, retries=1)"

