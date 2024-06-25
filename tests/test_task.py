import pytest
from unittest.mock import MagicMock
from neopipe.task import Task
from neopipe.result import Ok, Err
import logging

def test_task_success():
    # Test a task that succeeds
    def success_task(data):
        return Ok(data + 1)

    task = Task(success_task)
    result = task(1)
    assert result.is_ok()
    assert result.value == 2

def test_task_failure():
    # Test a task that fails
    def failure_task(data):
        return Err("Failure")

    task = Task(failure_task)
    result = task(1)
    assert result.is_err()
    assert result.error == "Failure"

def test_task_retries_success(mocker):
    # Test a task that succeeds after a retry
    mock = mocker.MagicMock()
    mock.__name__ = "mock"
    mock.side_effect = [Exception("Test exception"), Ok(2)]
    task = Task(mock, retries=2)
    result = task(1)
    assert result.is_ok()
    assert result.value == 2
    assert mock.call_count == 2


def test_task_retries_failure(mocker):
    # Test a task that raises an exception and retries
    mock = mocker.MagicMock()
    mock.__name__ = "mock"
    mock.side_effect = [Exception("Test exception"), Exception("Test exception")]

    task = Task(mock, retries=2)
    result = task(1)
    assert result.is_err()
    assert result.error == "Task mock failed after 2 attempts: Test exception"
    assert mock.call_count == 2

def test_task_exception_handling(mocker):
    # Test a task that raises an exception and retries
    mock = mocker.MagicMock()
    mock.__name__ = "mock"
    mock.side_effect = [Exception("Test exception"), Ok(2)]

    task = Task(mock, retries=2)
    result = task(1)
    assert result.is_ok()
    assert result.value == 2
    assert mock.call_count == 2

def test_task_exception_handling_failure(mocker):
    # Test a task that raises exceptions and fails after all retries
    mock = mocker.MagicMock()
    mock.__name__ = "mock"
    mock.side_effect = [Exception("Test exception"), Exception("Test exception")]

    task = Task(mock, retries=2)
    result = task(1)
    assert result.is_err()
    assert result.error == "Task mock failed after 2 attempts: Test exception"
    assert mock.call_count == 2

def test_task_logging(mocker, caplog):
    # Test logging output
    def success_task(data):
        return Ok(data + 1)

    mocker.patch('time.sleep', return_value=None)  # To avoid actual sleep during tests
    task = Task(success_task, retries=1)

    with caplog.at_level(logging.INFO):
        result = task(1)

    assert result.is_ok()
    assert "Executing task success_task" in caplog.text
    assert "Task success_task succeeded on attempt 1" in caplog.text



def dummy_task(data):
    return Ok(data)

def test_task_str():
    task = Task(dummy_task, retries=3)
    expected_str = "Task(dummy_task, retries=3)"
    assert str(task) == expected_str

def test_task_repr():
    task = Task(dummy_task, retries=3)
    expected_repr = "Task(dummy_task, retries=3)"
    assert repr(task) == expected_repr
