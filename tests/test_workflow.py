import asyncio
import pytest
from neopipe.result import Ok, Err
from neopipe.task import FunctionSyncTask, FunctionAsyncTask
from neopipe.workflow import SyncWorkflow, AsyncWorkflow


# Simple sync task for testing
@FunctionSyncTask.decorator()
def add_one_sync(result):
    if result.is_err():
        return result
    return Ok(result.unwrap() + 1)


# Simple async task for testing
@FunctionAsyncTask.decorator()
async def add_one_async(result):
    if result.is_err():
        return result
    await asyncio.sleep(0.01)  # Minimal async operation
    return Ok(result.unwrap() + 1)


def test_sync_workflow_inheritance():
    """Test that SyncWorkflow inherits from SyncPipeline and works correctly."""
    # Create a workflow with a single task
    workflow = SyncWorkflow.from_tasks([add_one_sync], name="TestSyncWorkflow")
    
    # Verify it's an instance of SyncWorkflow
    assert isinstance(workflow, SyncWorkflow)
    
    # Verify it has the expected name
    assert workflow.name == "TestSyncWorkflow"
    
    # Test basic functionality - run the workflow
    result = workflow.run(Ok(5))
    
    # Verify the result
    assert result.result.is_ok()
    assert result.result.unwrap() == 6
    assert result.execution_time > 0


@pytest.mark.asyncio
async def test_async_workflow_inheritance():
    """Test that AsyncWorkflow inherits from AsyncPipeline and works correctly."""
    # Create a workflow with a single task
    workflow = AsyncWorkflow.from_tasks([add_one_async], name="TestAsyncWorkflow")
    
    # Verify it's an instance of AsyncWorkflow
    assert isinstance(workflow, AsyncWorkflow)
    
    # Verify it has the expected name
    assert workflow.name == "TestAsyncWorkflow"
    
    # Test basic functionality - run the workflow sequentially
    result = await workflow.run_sequence(Ok(10))
    
    # Verify the result
    assert result.result.is_ok()
    assert result.result.unwrap() == 11
    assert result.execution_time > 0


def test_sync_workflow_error_handling():
    """Test that SyncWorkflow properly handles errors like SyncPipeline."""
    workflow = SyncWorkflow.from_tasks([add_one_sync], name="ErrorTestWorkflow")
    
    # Pass an error and verify it's propagated
    error_input = Err("test error")
    result = workflow.run(error_input)
    
    assert result.result.is_err()
    assert result.result.unwrap_err() == "test error"


@pytest.mark.asyncio
async def test_async_workflow_error_handling():
    """Test that AsyncWorkflow properly handles errors like AsyncPipeline."""
    workflow = AsyncWorkflow.from_tasks([add_one_async], name="ErrorTestAsyncWorkflow")
    
    # Pass an error and verify it's propagated
    error_input = Err("async test error")
    result = await workflow.run_sequence(error_input)
    
    assert result.result.is_err()
    assert result.result.unwrap_err() == "async test error"