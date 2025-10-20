# Workflow Classes Example

This example demonstrates how to use `SyncWorkflow` and `AsyncWorkflow` classes as alternative namespaces for pipeline functionality.

## Overview

Workflow classes provide the same functionality as pipelines but with workflow-oriented terminology:
- `SyncWorkflow` - Inherits from `SyncPipeline`
- `AsyncWorkflow` - Inherits from `AsyncPipeline`

These classes are useful when you want to emphasize the workflow nature of your process rather than the pipeline implementation.

## Basic Sync Workflow

```python
from neopipe import Ok, Err, SyncWorkflow
from neopipe.task import FunctionSyncTask

# Define workflow steps
@FunctionSyncTask.decorator()
def validate_input(result):
    """Validate the input data."""
    if result.is_err():
        return result
    
    data = result.unwrap()
    if not isinstance(data, dict) or 'user_id' not in data:
        return Err("Invalid input: missing user_id")
    
    return Ok(data)

@FunctionSyncTask.decorator()
def enrich_data(result):
    """Enrich the data with additional information."""
    if result.is_err():
        return result
    
    data = result.unwrap()
    data['timestamp'] = '2025-10-20'
    data['status'] = 'active'
    
    return Ok(data)

@FunctionSyncTask.decorator()
def format_output(result):
    """Format the final output."""
    if result.is_err():
        return result
    
    data = result.unwrap()
    formatted = {
        'user': data['user_id'],
        'created_at': data['timestamp'],
        'active': data['status'] == 'active'
    }
    
    return Ok(formatted)

# Create and run the workflow
def user_processing_workflow():
    # Create workflow instance
    workflow = SyncWorkflow.from_tasks(
        tasks=[validate_input, enrich_data, format_output],
        name="UserProcessingWorkflow"
    )
    
    # Input data
    user_data = Ok({'user_id': '12345', 'name': 'Alice'})
    
    # Execute workflow
    result = workflow.run(user_data, debug=True)
    
    if result.result.is_ok():
        print("✅ Workflow completed successfully!")
        print(f"Result: {result.result.unwrap()}")
    else:
        print("❌ Workflow failed!")
        print(f"Error: {result.result.unwrap_err()}")
    
    print(f"Execution time: {result.execution_time:.3f}s")
    
    # Show workflow trace
    if result.trace:
        print("\n📋 Workflow Execution Trace:")
        for step_name, step_result in result.trace.steps:
            status = "✅" if step_result.is_ok() else "❌"
            print(f"  {status} {step_name}")

# Run the example
user_processing_workflow()
```

## Async Workflow Example

```python
import asyncio
from neopipe import Ok, Err, AsyncWorkflow
from neopipe.task import FunctionAsyncTask

# Define async workflow steps
@FunctionAsyncTask.decorator()
async def fetch_user_data(result):
    """Simulate fetching user data from an API."""
    if result.is_err():
        return result
    
    user_id = result.unwrap()
    
    # Simulate API call
    await asyncio.sleep(0.1)
    
    if user_id == "invalid":
        return Err("User not found")
    
    user_data = {
        'id': user_id,
        'name': f'User_{user_id}',
        'email': f'user{user_id}@example.com'
    }
    
    return Ok(user_data)

@FunctionAsyncTask.decorator()
async def calculate_metrics(result):
    """Calculate user metrics."""
    if result.is_err():
        return result
    
    user_data = result.unwrap()
    
    # Simulate metric calculation
    await asyncio.sleep(0.05)
    
    metrics = {
        'user_data': user_data,
        'login_count': 42,
        'last_active': '2025-10-20',
        'score': 85.5
    }
    
    return Ok(metrics)

@FunctionAsyncTask.decorator()
async def generate_report(result):
    """Generate final user report."""
    if result.is_err():
        return result
    
    metrics = result.unwrap()
    
    # Simulate report generation
    await asyncio.sleep(0.02)
    
    report = {
        'user': metrics['user_data']['name'],
        'email': metrics['user_data']['email'],
        'activity_score': metrics['score'],
        'status': 'active' if metrics['login_count'] > 0 else 'inactive',
        'generated_at': '2025-10-20T10:00:00Z'
    }
    
    return Ok(report)

async def user_analytics_workflow():
    """Async workflow for user analytics."""
    
    # Create async workflow
    workflow = AsyncWorkflow.from_tasks(
        tasks=[fetch_user_data, calculate_metrics, generate_report],
        name="UserAnalyticsWorkflow"
    )
    
    # Process multiple users concurrently
    user_ids = [Ok("123"), Ok("456"), Ok("789"), Ok("invalid")]
    
    print("🚀 Starting concurrent user processing...")
    
    # Run workflow concurrently for multiple users
    results = await workflow.run(user_ids, debug=True)
    
    print(f"\n📊 Processing completed in {results.execution_time:.3f}s")
    
    # Display results
    for i, result in enumerate(results.result):
        user_id = user_ids[i].unwrap() if user_ids[i].is_ok() else "unknown"
        
        if result.is_ok():
            report = result.unwrap()
            print(f"✅ User {user_id}: {report['user']} - Score: {report['activity_score']}")
        else:
            print(f"❌ User {user_id}: {result.unwrap_err()}")
    
    # Show trace information
    if results.trace and results.trace.pipelines:
        print(f"\n📋 Processed {len(results.trace.pipelines)} user workflows")

# Run async example
asyncio.run(user_analytics_workflow())
```

## Workflow vs Pipeline Comparison

```python
# Both approaches are functionally identical
from neopipe import SyncPipeline, SyncWorkflow

# Pipeline approach - emphasizes data flow
pipeline = SyncPipeline.from_tasks([task1, task2, task3], name="DataPipeline")
result = pipeline.run(input_data)

# Workflow approach - emphasizes business process
workflow = SyncWorkflow.from_tasks([task1, task2, task3], name="BusinessWorkflow")
result = workflow.run(input_data)

# Both inherit the same methods and functionality
assert type(pipeline.run) == type(workflow.run)
assert hasattr(workflow, 'add_task')
assert hasattr(workflow, 'replicate_task')
```

## Business Process Workflow

```python
from neopipe import Ok, Err, SyncWorkflow
from neopipe.task import ClassSyncTask

class OrderValidationTask(ClassSyncTask):
    """Validate order details."""
    
    def execute(self, result):
        if result.is_err():
            return result
        
        order = result.unwrap()
        
        # Validation logic
        if order.get('amount', 0) <= 0:
            return Err("Invalid order amount")
        
        if not order.get('customer_id'):
            return Err("Missing customer ID")
        
        return Ok({**order, 'validated': True})

class PaymentProcessingTask(ClassSyncTask):
    """Process payment for the order."""
    
    def execute(self, result):
        if result.is_err():
            return result
        
        order = result.unwrap()
        
        # Simulate payment processing
        if order['amount'] > 10000:
            return Err("Payment declined: amount too high")
        
        return Ok({**order, 'payment_status': 'completed', 'transaction_id': 'txn_123'})

class FulfillmentTask(ClassSyncTask):
    """Handle order fulfillment."""
    
    def execute(self, result):
        if result.is_err():
            return result
        
        order = result.unwrap()
        
        # Fulfillment logic
        return Ok({
            **order, 
            'fulfillment_status': 'shipped',
            'tracking_number': 'TRK123456789'
        })

def order_processing_workflow():
    """Complete order processing workflow."""
    
    # Create business workflow
    workflow = SyncWorkflow.from_tasks([
        OrderValidationTask(),
        PaymentProcessingTask(), 
        FulfillmentTask()
    ], name="OrderProcessingWorkflow")
    
    # Sample order
    order = Ok({
        'order_id': 'ORD001',
        'customer_id': 'CUST123',
        'amount': 99.99,
        'items': ['item1', 'item2']
    })
    
    # Process order through workflow
    result = workflow.run(order, debug=True)
    
    if result.result.is_ok():
        final_order = result.result.unwrap()
        print("🎉 Order processed successfully!")
        print(f"Order ID: {final_order['order_id']}")
        print(f"Transaction: {final_order['transaction_id']}")
        print(f"Tracking: {final_order['tracking_number']}")
    else:
        print(f"❌ Order processing failed: {result.result.unwrap_err()}")
    
    return result

# Run order processing
order_result = order_processing_workflow()
```

## Key Benefits of Workflow Classes

1. **Semantic Clarity**: Use when emphasizing business processes over data pipelines
2. **Full Compatibility**: All pipeline methods and features available
3. **Team Communication**: Clearer for non-technical stakeholders
4. **Documentation**: Self-documenting code with workflow terminology
5. **Future Extensions**: Room for workflow-specific features

## When to Use Workflows vs Pipelines

### Use `SyncWorkflow`/`AsyncWorkflow` when:
- Modeling business processes
- Working with domain experts who think in workflows
- Building process automation systems
- Emphasizing the sequence of business steps

### Use `SyncPipeline`/`AsyncPipeline` when:
- Focusing on data transformation
- Building data processing systems
- Emphasizing technical data flow
- Working primarily with technical teams

## Best Practices

1. **Consistent Naming**: Choose either workflow or pipeline terminology consistently
2. **Documentation**: Use workflow terminology in comments and docs when using workflow classes
3. **Task Naming**: Use business-oriented task names with workflows
4. **Error Messages**: Frame errors in business context for workflows
5. **Monitoring**: Use workflow-oriented metrics and logging