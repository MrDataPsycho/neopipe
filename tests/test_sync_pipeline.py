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
