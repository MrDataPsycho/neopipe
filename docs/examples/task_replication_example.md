# Task Replication Example

This example demonstrates how to use the `replicate_task` functionality to create multiple instances of a task for parallel processing.

## Overview

The `replicate_task` method allows you to create multiple copies of a task with unique IDs, which is useful for:
- Processing multiple data items in parallel
- Load balancing across multiple task instances
- Scaling specific parts of your pipeline

## Basic Example

```python
import asyncio
from neopipe import Ok, Err, SyncPipeline, AsyncPipeline
from neopipe.task import FunctionSyncTask, FunctionAsyncTask

# Define a data processing task
@FunctionSyncTask.decorator()
def process_data(result):
    """Simulate data processing that takes some time."""
    if result.is_err():
        return result
    
    data = result.unwrap()
    # Simulate processing time
    import time
    time.sleep(0.1)
    
    return Ok(f"processed_{data}")

# Create a pipeline and replicate the task
pipeline = SyncPipeline(name="DataProcessingPipeline")

# Replicate the task 3 times for parallel processing
replicated_tasks = pipeline.replicate_task(process_data, num_replicas=3)

print(f"Created {len(replicated_tasks)} task replicas")
for i, task in enumerate(replicated_tasks):
    print(f"Task {i+1} ID: {task.task_id}")
```

## Parallel Processing Example

```python
# Use replicated tasks for parallel processing
def parallel_processing_example():
    # Create multiple pipelines with replicated tasks
    pipelines = []
    for i in range(3):
        pipeline = SyncPipeline(name=f"Pipeline_{i+1}")
        # Each pipeline gets its own replica of the task
        replicated_tasks = pipeline.replicate_task(process_data, num_replicas=1)
        pipeline.add_task(replicated_tasks[0])
        pipelines.append(pipeline)
    
    # Input data to process
    inputs = [Ok("data_1"), Ok("data_2"), Ok("data_3")]
    
    # Process in parallel
    results = SyncPipeline.run_parallel(
        pipelines=pipelines,
        inputs=inputs,
        max_workers=3,
        debug=True
    )
    
    print("Parallel processing results:")
    for i, result in enumerate(results.result):
        if result.is_ok():
            print(f"Pipeline {i+1}: {result.unwrap()}")
        else:
            print(f"Pipeline {i+1}: Error - {result.unwrap_err()}")
    
    print(f"Total execution time: {results.execution_time:.2f}s")

# Run the example
parallel_processing_example()
```

## Async Task Replication

```python
@FunctionAsyncTask.decorator()
async def async_process_data(result):
    """Async version of data processing."""
    if result.is_err():
        return result
    
    data = result.unwrap()
    # Simulate async processing
    await asyncio.sleep(0.1)
    
    return Ok(f"async_processed_{data}")

async def async_replication_example():
    # Create async pipeline with replicated tasks
    pipeline = AsyncPipeline(name="AsyncDataPipeline")
    
    # Replicate async task
    replicated_tasks = pipeline.replicate_task(async_process_data, num_replicas=2)
    
    # Add tasks to pipeline
    for task in replicated_tasks:
        pipeline.add_task(task)
    
    # Process data through the pipeline
    result = await pipeline.run_sequence(Ok("async_data"), debug=True)
    
    print(f"Async processing result: {result.result.unwrap()}")
    print(f"Execution time: {result.execution_time:.2f}s")
    
    # Show trace information
    if result.trace:
        print("\nExecution trace:")
        for step_name, step_result in result.trace.steps:
            status = "✅" if step_result.is_ok() else "❌"
            print(f"  {status} {step_name}")

# Run async example
asyncio.run(async_replication_example())
```

## Use Cases

### 1. Load Balancing
```python
# Replicate a heavy computation task for load balancing
heavy_task = create_heavy_computation_task()
replicas = pipeline.replicate_task(heavy_task, num_replicas=5)

# Distribute work across replicas
for i, replica in enumerate(replicas):
    worker_pipeline = SyncPipeline(name=f"Worker_{i+1}")
    worker_pipeline.add_task(replica)
```

### 2. Fault Tolerance
```python
# Create multiple replicas for redundancy
unreliable_task = create_network_request_task()
backup_tasks = pipeline.replicate_task(unreliable_task, num_replicas=3)

# Try each replica until one succeeds
for task in backup_tasks:
    result = task(input_data)
    if result.is_ok():
        break
```

### 3. A/B Testing
```python
# Replicate task with different configurations
base_task = create_ml_model_task()
variants = pipeline.replicate_task(base_task, num_replicas=2)

# Configure different model parameters
variants[0].config = {"model": "version_a"}
variants[1].config = {"model": "version_b"}

# Compare results
results_a = variants[0](test_data)
results_b = variants[1](test_data)
```

## Key Benefits

- **Unique IDs**: Each replicated task gets a unique `task_id` for tracking
- **Independent State**: Deep copying ensures replicas don't share mutable state
- **Flexible Usage**: Can be used in both sync and async pipelines
- **Scalability**: Easy to scale specific bottleneck tasks
- **Debugging**: Each replica can be traced independently

## Best Practices

1. **Resource Management**: Be mindful of memory usage when creating many replicas
2. **Task Design**: Ensure tasks are stateless or properly handle state isolation
3. **Error Handling**: Use debug mode to trace issues across replicated tasks
4. **Performance**: Measure actual performance gains from replication
5. **Monitoring**: Track individual replica performance using unique task IDs