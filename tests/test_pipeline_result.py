import pytest
from neopipe.result import Ok, Err, Trace, Traces, ExecutionResult

def test_trace_basic():
    """
    Trace should store a list of (task_name, Result) steps,
    report its length correctly, and have a repr including its data.
    """
    steps = [("t1", Ok(1)), ("t2", Err("e"))]
    trace = Trace(steps=steps)
    assert len(trace) == 2
    assert repr(trace) == f"Trace(steps={steps!r})"
    assert trace.steps == steps

def test_traces_basic():
    """
    Traces should store multiple Trace instances,
    report its length correctly, and have a repr including its data.
    """
    trace1 = Trace(steps=[("a", Ok(10))])
    trace2 = Trace(steps=[("b", Err("err"))])
    traces = Traces(pipelines=[trace1, trace2])
    assert len(traces) == 2
    assert repr(traces) == f"Traces(pipelines={[trace1, trace2]!r})"
    assert traces.pipelines == [trace1, trace2]

def test_execution_result_single_success():
    """
    ExecutionResult for a single-ok should:
      - unwrap via .value()
      - report length == 1
      - have repr containing the Ok value
    """
    er = ExecutionResult(result=Ok(5), trace=None, execution_time=0.123)
    assert er.value() == 5
    assert len(er) == 1
    rep = repr(er)
    assert "ExecutionResult" in rep and "Ok(5)" in rep

def test_execution_result_single_err():
    """
    ExecutionResult for a single-err should:
      - .value() raise
      - report length == 1
    """
    er = ExecutionResult(result=Err("oops"), trace=None, execution_time=0.05)
    with pytest.raises(Exception):
        _ = er.value()
    assert len(er) == 1

def test_execution_result_list_all_ok():
    """
    ExecutionResult for a list of Ok results should unwrap all values
    and report the correct length.
    """
    results = [Ok(2), Ok(3), Ok(4)]
    er = ExecutionResult(result=results, trace=None, execution_time=0.2)
    assert er.value() == [2, 3, 4]
    assert len(er) == 3

def test_execution_result_list_with_err():
    """
    ExecutionResult for a list containing an Err should make .value()
    raise and still report correct length.
    """
    results = [Ok(1), Err("bad"), Ok(5)]
    er = ExecutionResult(result=results, trace=None, execution_time=0.2)
    with pytest.raises(Exception):
        _ = er.value()
    assert len(er) == 3
