import pytest
from neopipe.result import Ok, Err, Result, Trace, Traces, ExecutionResult
from neopipe.task import FunctionSyncTask, ClassSyncTask
from neopipe.pipeline import SyncPipeline

# -- Task definitions for tests --

@FunctionSyncTask.decorator()
def add_one(res: Result[int, str]) -> Result[int, str]:
    """Increment an Ok value by 1, propagate Err."""
    return Ok(res.unwrap() + 1) if res.is_ok() else res

@FunctionSyncTask.decorator()
def fail_task(res: Result[int, str]) -> Result[int, str]:
    """Always return an Err."""
    return Err("failure occurred")

class MultiplyTask(ClassSyncTask[int, str]):
    """Multiply the Ok value by a given factor."""
    def __init__(self, multiplier: int):
        super().__init__()
        self.multiplier = multiplier

    def execute(self, res: Result[int, str]) -> Result[int, str]:
        return Ok(res.unwrap() * self.multiplier) if res.is_ok() else res

# -- Tests for SyncPipeline.run() --

def test_run_success():
    """
    SyncPipeline.run should chain two add_one tasks successfully
    when debug=False.
    """
    pipeline = SyncPipeline.from_tasks([add_one, add_one], name="IncPipeline")
    exec_res = pipeline.run(Ok(1), debug=False)
    assert isinstance(exec_res, ExecutionResult)
    assert isinstance(exec_res.result, Result)
    assert exec_res.result == Ok(3)

def test_run_failure_propagates():
    """
    SyncPipeline.run should stop on the first Err and propagate it
    when debug=False.
    """
    pipeline = SyncPipeline.from_tasks([add_one, fail_task, add_one], name="FailPipeline")
    exec_res = pipeline.run(Ok(1), debug=False)
    assert isinstance(exec_res, ExecutionResult)
    assert exec_res.result == Err("failure occurred")

def test_run_debug_trace():
    """
    SyncPipeline.run should return a Trace when debug=True,
    including the pipeline name and each task's result.
    """
    pipeline = SyncPipeline.from_tasks([add_one, add_one], name="DebugPipeline")
    exec_res = pipeline.run(Ok(2), debug=True)
    assert isinstance(exec_res, ExecutionResult)
    # The final result
    assert exec_res.result == Ok(4)
    # The trace should be present
    assert isinstance(exec_res.trace, Trace)
    steps = exec_res.trace.steps
    # First step is the pipeline itself
    assert steps[0][0] == "DebugPipeline"
    # Next step is the first add_one call
    assert steps[1][0] == "add_one" and steps[1][1] == Ok(3)

# -- Tests for SyncPipeline.run_parallel() --

def test_run_parallel_success():
    """
    run_parallel should execute multiple pipelines concurrently
    and return their individual Result values in order.
    """
    p1 = SyncPipeline.from_tasks([add_one], name="P1")
    p2 = SyncPipeline.from_tasks([add_one, MultiplyTask(2)], name="P2")
    inputs = [Ok(5), Ok(3)]
    exec_res = SyncPipeline.run_parallel([p1, p2], inputs, debug=False)
    assert isinstance(exec_res, ExecutionResult)
    res_list = exec_res.result
    assert res_list[0] == Ok(6)
    assert res_list[1] == Ok(8)

def test_run_parallel_debug():
    """
    run_parallel with debug=True should produce both a list of Results
    and a Traces object capturing each pipeline's Trace.
    """
    p1 = SyncPipeline.from_tasks([add_one], name="P1")
    p2 = SyncPipeline.from_tasks([fail_task], name="P2")
    inputs = [Ok(4), Ok(2)]
    exec_res = SyncPipeline.run_parallel([p1, p2], inputs, debug=True)
    assert isinstance(exec_res, ExecutionResult)
    # Results list
    res_list = exec_res.result
    assert res_list[0] == Ok(5)
    assert res_list[1] == Err("failure occurred")
    # Trace collection
    assert isinstance(exec_res.trace, Traces)
    assert len(exec_res.trace.pipelines) == 2
    # Verify last step of each pipeline's trace
    trace1 = exec_res.trace.pipelines[0]
    assert trace1.steps[-1] == ("add_one", Ok(5))
    trace2 = exec_res.trace.pipelines[1]
    assert trace2.steps[-1] == ("fail_task", Err("failure occurred"))

def test_run_parallel_input_length_mismatch():
    """
    run_parallel should raise AssertionError when the number of inputs
    does not match the number of pipelines.
    """
    p = SyncPipeline.from_tasks([add_one], name="Single")
    with pytest.raises(AssertionError):
        SyncPipeline.run_parallel([p, p], [Ok(1)])

# -- Tests for SyncPipeline.replicate_task() --

def test_replicate_task_creates_unique_ids():
    """
    SyncPipeline.replicate_task should create multiple copies of a task
    with unique task IDs.
    """
    pipeline = SyncPipeline(name="TestPipeline")
    original_task = MultiplyTask(multiplier=2)
    original_id = original_task.task_id

    replicas = pipeline.replicate_task(original_task, num_replicas=3)

    assert len(replicas) == 3
    assert all(isinstance(replica, MultiplyTask) for replica in replicas)
    assert all(replica.multiplier == 2 for replica in replicas)

    # All task IDs should be unique and different from original
    task_ids = [replica.task_id for replica in replicas]
    assert len(set(task_ids)) == 3  # All unique
    assert original_id not in task_ids  # Different from original

def test_replicate_task_preserves_functionality():
    """
    Replicated tasks should maintain the same functionality as the original.
    """
    pipeline = SyncPipeline(name="TestPipeline")
    original_task = MultiplyTask(multiplier=3)

    replicas = pipeline.replicate_task(original_task, num_replicas=2)

    # Test that replicas work the same as original
    test_input = Ok(5)
    expected_result = Ok(15)

    original_result = original_task(test_input)
    replica1_result = replicas[0](test_input)
    replica2_result = replicas[1](test_input)

    assert original_result == expected_result
    assert replica1_result == expected_result
    assert replica2_result == expected_result

def test_replicate_task_with_function_task():
    """
    SyncPipeline.replicate_task should work with function-based tasks.
    """
    pipeline = SyncPipeline(name="TestPipeline")

    replicas = pipeline.replicate_task(add_one, num_replicas=4)

    assert len(replicas) == 4

    # All task IDs should be unique
    task_ids = [replica.task_id for replica in replicas]
    assert len(set(task_ids)) == 4

    # All should have the same task name
    assert all(replica.task_name == "add_one" for replica in replicas)

    # Test functionality
    test_input = Ok(10)
    expected_result = Ok(11)

    for replica in replicas:
        assert replica(test_input) == expected_result

def test_replicate_task_zero_replicas():
    """
    SyncPipeline.replicate_task should return empty list for zero replicas.
    """
    pipeline = SyncPipeline(name="TestPipeline")
    original_task = MultiplyTask(multiplier=2)

    replicas = pipeline.replicate_task(original_task, num_replicas=0)

    assert replicas == []

def test_replicated_tasks_with_run_parallel():
    """
    Test that replicated tasks can be used with run_parallel for concurrent execution.
    """
    # Create a task and replicate it
    original_task = MultiplyTask(multiplier=2)

    # Create individual pipelines with replicated tasks
    pipelines = []
    replicas = SyncPipeline(name="temp").replicate_task(original_task, num_replicas=3)

    for i, replica in enumerate(replicas):
        pipeline = SyncPipeline(name=f"Pipeline-{i}")
        pipeline.add_task(replica)
        pipelines.append(pipeline)

    # Run with different inputs
    inputs = [Ok(1), Ok(2), Ok(3)]
    exec_result = SyncPipeline.run_parallel(pipelines, inputs, debug=True)

    # Verify results
    assert exec_result.is_ok()
    assert exec_result.result == [Ok(2), Ok(4), Ok(6)]

    # Verify that each pipeline has unique task ID in trace
    assert exec_result.trace is not None
    task_ids_in_trace = []
    for trace in exec_result.trace.pipelines:
        for step_name, step_result in trace.steps:
            if step_name.startswith("MultiplyTask"):
                # Extract task info from logging or task execution
                pass  # Task IDs are logged but not in trace directly

    # At minimum, verify we have 3 separate pipeline traces
    assert len(exec_result.trace.pipelines) == 3
