import pytest
import asyncio
from neopipe.result import Ok, Err, Result, Trace, ExecutionResult
from neopipe.task import FunctionAsyncTask, ClassAsyncTask
from neopipe.async_pipeline import AsyncPipeline

# -- Task definitions for async tests --

@FunctionAsyncTask.decorator()
async def add_one_async(res: Result[int, str]) -> Result[int, str]:
    """Increment an Ok value by 1, propagate Err."""
    if res.is_ok():
        return Ok(res.unwrap() + 1)
    return res

@FunctionAsyncTask.decorator()
async def fail_async(res: Result[int, str]) -> Result[int, str]:
    """Always return an Err."""
    return Err("failure occurred")

class MultiplyAsync(ClassAsyncTask[int, str]):
    """Multiply the Ok value by a given factor asynchronously."""
    def __init__(self, multiplier: int):
        super().__init__()
        self.multiplier = multiplier

    async def execute(self, res: Result[int, str]) -> Result[int, str]:
        if res.is_ok():
            return Ok(res.unwrap() * self.multiplier)
        return res

# ----------------------------
# tests/test_async_pipeline.py
# ----------------------------

@pytest.mark.asyncio
async def test_run_concurrent_success():
    """
    AsyncPipeline.run should execute tasks concurrently, returning
    an ExecutionResult with .result as a list of Result values,
    and no trace when debug=False.
    """
    pipeline = AsyncPipeline.from_tasks([add_one_async, add_one_async], name="IncAsync")
    inputs = [Ok(1), Ok(2)]
    exec_res = await pipeline.run(inputs, debug=False)

    assert isinstance(exec_res, ExecutionResult)
    # .result is a list of Result[int, str]
    assert isinstance(exec_res.result, list)
    assert exec_res.result == [Ok(2), Ok(3)]
    # No trace when debug=False
    assert exec_res.trace is None

@pytest.mark.asyncio
async def test_run_concurrent_debug():
    """
    AsyncPipeline.run with debug=True should produce both the list of Results
    and a Trace object with one entry per task.
    """
    pipeline = AsyncPipeline.from_tasks([add_one_async, add_one_async], name="IncAsync")
    inputs = [Ok(5), Ok(6)]
    exec_res = await pipeline.run(inputs, debug=True)

    assert isinstance(exec_res, ExecutionResult)
    assert exec_res.result == [Ok(6), Ok(7)]
    # Trace should record each task's name and Result
    assert isinstance(exec_res.trace, Trace)
    steps = exec_res.trace.steps
    assert steps == [("add_one_async", Ok(6)), ("add_one_async", Ok(7))]

@pytest.mark.asyncio
async def test_run_sequence_success():
    """
    AsyncPipeline.run_sequence should chain tasks in sequence,
    returning ExecutionResult.result as a single Result,
    and no trace when debug=False.
    """
    pipeline = AsyncPipeline.from_tasks([add_one_async, add_one_async], name="SeqAsync")
    exec_res = await pipeline.run_sequence(Ok(3), debug=False)

    assert isinstance(exec_res, ExecutionResult)
    assert isinstance(exec_res.result, Result)
    assert exec_res.result == Ok(5)
    assert exec_res.trace is None

@pytest.mark.asyncio
async def test_run_sequence_debug_error():
    """
    AsyncPipeline.run_sequence with debug=True should include all steps
    even after a failure, recording both successes and the Err.
    """
    pipeline = AsyncPipeline.from_tasks(
        [add_one_async, fail_async, add_one_async],
        name="SeqAsyncErr"
    )
    exec_res = await pipeline.run_sequence(Ok(2), debug=True)

    assert isinstance(exec_res, ExecutionResult)
    # Final result is Err
    assert exec_res.result == Err("failure occurred")
    # Trace should record each step up to the failure
    assert isinstance(exec_res.trace, Trace)
    steps = exec_res.trace.steps
    assert steps[0] == ("add_one_async", Ok(3))
    assert steps[1] == ("fail_async", Err("failure occurred"))

@pytest.mark.asyncio
async def test_run_parallel_success():
    """
    AsyncPipeline.run_parallel should run multiple pipelines concurrently,
    returning an ExecutionResult with .result as a list of Result values.
    """
    p1 = AsyncPipeline.from_tasks([add_one_async], name="P1")
    p2 = AsyncPipeline.from_tasks([add_one_async, MultiplyAsync(3)], name="P2")
    inputs = [Ok(4), Ok(5)]

    exec_res = await AsyncPipeline.run_parallel([p1, p2], inputs, debug=False)

    assert isinstance(exec_res, ExecutionResult)
    # .result is a list of Result[int, str]
    assert exec_res.result == [Ok(5), Ok(18)]
    assert exec_res.trace is None

@pytest.mark.asyncio
async def test_run_parallel_input_length_mismatch():
    """
    AsyncPipeline.run_parallel should raise AssertionError if the number of inputs
    does not match the number of pipelines.
    """
    p = AsyncPipeline.from_tasks([add_one_async], name="Single")
    with pytest.raises(AssertionError):
        await AsyncPipeline.run_parallel([p, p], [Ok(1)])

@pytest.mark.asyncio
async def test_run_parallel_unhandled_exception():
    """
    If a pipeline.run_sequence raises an exception, run_parallel should catch it
    and include an Err in the results list, without crashing.
    """
    class BadAsyncPipeline(AsyncPipeline[int, str]):
        async def run_sequence(self, *args, **kwargs):
            raise RuntimeError("boom")

    bad = BadAsyncPipeline(name="Bad")
    good = AsyncPipeline.from_tasks([add_one_async], name="Good")
    inputs = [Ok(1), Ok(2)]

    exec_res = await AsyncPipeline.run_parallel([good, bad], inputs, debug=False)

    assert isinstance(exec_res, ExecutionResult)
    # Good pipeline result
    assert exec_res.result[0] == Ok(2)
    # Bad pipeline captured exception as Err
    assert exec_res.result[1].is_err()
    assert "boom" in exec_res.result[1].err()

# -- Tests for AsyncPipeline.replicate_task() --

@pytest.mark.asyncio
async def test_replicate_task_creates_unique_ids():
    """
    AsyncPipeline.replicate_task should create multiple copies of a task
    with unique task IDs.
    """
    pipeline = AsyncPipeline(name="TestAsyncPipeline")
    original_task = MultiplyAsync(multiplier=2)
    original_id = original_task.task_id

    replicas = pipeline.replicate_task(original_task, num_replicas=3)

    assert len(replicas) == 3
    assert all(isinstance(replica, MultiplyAsync) for replica in replicas)
    assert all(replica.multiplier == 2 for replica in replicas)

    # All task IDs should be unique and different from original
    task_ids = [replica.task_id for replica in replicas]
    assert len(set(task_ids)) == 3  # All unique
    assert original_id not in task_ids  # Different from original

@pytest.mark.asyncio
async def test_replicate_task_preserves_functionality():
    """
    Replicated async tasks should maintain the same functionality as the original.
    """
    pipeline = AsyncPipeline(name="TestAsyncPipeline")
    original_task = MultiplyAsync(multiplier=3)

    replicas = pipeline.replicate_task(original_task, num_replicas=2)

    # Test that replicas work the same as original
    test_input = Ok(5)
    expected_result = Ok(15)

    original_result = await original_task(test_input)
    replica1_result = await replicas[0](test_input)
    replica2_result = await replicas[1](test_input)

    assert original_result == expected_result
    assert replica1_result == expected_result
    assert replica2_result == expected_result

@pytest.mark.asyncio
async def test_replicate_task_with_function_task():
    """
    AsyncPipeline.replicate_task should work with function-based async tasks.
    """
    pipeline = AsyncPipeline(name="TestAsyncPipeline")

    replicas = pipeline.replicate_task(add_one_async, num_replicas=4)

    assert len(replicas) == 4

    # All task IDs should be unique
    task_ids = [replica.task_id for replica in replicas]
    assert len(set(task_ids)) == 4

    # All should have the same task name
    assert all(replica.task_name == "add_one_async" for replica in replicas)

    # Test functionality
    test_input = Ok(10)
    expected_result = Ok(11)

    for replica in replicas:
        result = await replica(test_input)
        assert result == expected_result

@pytest.mark.asyncio
async def test_replicate_task_zero_replicas():
    """
    AsyncPipeline.replicate_task should return empty list for zero replicas.
    """
    pipeline = AsyncPipeline(name="TestAsyncPipeline")
    original_task = MultiplyAsync(multiplier=2)

    replicas = pipeline.replicate_task(original_task, num_replicas=0)

    assert replicas == []

@pytest.mark.asyncio
async def test_replicated_tasks_with_run_parallel():
    """
    Test that replicated async tasks can be used with run_parallel for concurrent execution.
    """
    # Create a task and replicate it
    original_task = MultiplyAsync(multiplier=2)

    # Create individual pipelines with replicated tasks
    pipelines = []
    replicas = AsyncPipeline(name="temp").replicate_task(original_task, num_replicas=3)

    for i, replica in enumerate(replicas):
        pipeline = AsyncPipeline(name=f"AsyncPipeline-{i}")
        pipeline.add_task(replica)
        pipelines.append(pipeline)

    # Run with different inputs
    inputs = [Ok(1), Ok(2), Ok(3)]
    exec_result = await AsyncPipeline.run_parallel(pipelines, inputs, debug=True)

    # Verify results
    assert exec_result.is_ok()
    assert exec_result.result == [Ok(2), Ok(4), Ok(6)]

    # Verify that we have 3 separate pipeline traces
    assert exec_result.trace is not None
    assert len(exec_result.trace.pipelines) == 3

@pytest.mark.asyncio
async def test_replicated_tasks_with_run_concurrent():
    """
    Test that replicated async tasks can be used with run() for concurrent execution.
    """
    pipeline = AsyncPipeline(name="ConcurrentTest")
    original_task = MultiplyAsync(multiplier=3)

    # Add replicated tasks to the same pipeline
    replicas = pipeline.replicate_task(original_task, num_replicas=3)
    for replica in replicas:
        pipeline.add_task(replica)

    # Run with different inputs (each task gets one input)
    inputs = [Ok(1), Ok(2), Ok(3)]
    exec_result = await pipeline.run(inputs, debug=True)

    # Verify results
    assert exec_result.is_ok()
    assert exec_result.result == [Ok(3), Ok(6), Ok(9)]

    # Verify trace contains all replicated tasks
    assert exec_result.trace is not None
    assert len(exec_result.trace.steps) == 3

    # Check that all task names are the same but results are different
    task_names = [step[0] for step in exec_result.trace.steps]
    assert all(name == "MultiplyAsync" for name in task_names)
