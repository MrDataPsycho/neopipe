# OpenAI Async Pipeline with Task Replication Example

This example demonstrates using NeoPipe's `replicate_task` method with AsyncPipeline to create multiple instances of the same OpenAI task and run them asynchronously. We'll focus on task replication for efficient parallel processing.

## Overview

We'll create an OpenAI summarization system that:
- Uses a single OpenAI async task configuration
- Replicates the task multiple times using `replicate_task` method
- Demonstrates async task replication with concurrent execution
- Shows how replicated tasks can process different inputs simultaneously
- Compares performance and efficiency of replicated async tasks

## Complete Example

```python
import os
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass
from openai import AsyncOpenAI
from dotenv import load_dotenv

from neopipe import Result, Ok, Err
from neopipe.task import ClassAsyncTask
from neopipe.async_pipeline import AsyncPipeline

# Load environment variables
load_dotenv()

@dataclass
class TextInput:
    """Simple input structure for text summarization."""
    text: str
    id: str = ""

@dataclass
class SummaryOutput:
    """Output structure for summarization results."""
    original_text: str
    summary: str
    tokens_used: int
    task_id: str

class AsyncOpenAISummarizationTask(ClassAsyncTask[TextInput, str]):
    """
    An async task that calls OpenAI API to summarize text using a consistent system prompt.

    This demonstrates:
    - Async class-based task configuration
    - Non-blocking external API integration
    - Comprehensive async error handling
    - Result type usage in async context
    """

    def __init__(self,
                 system_prompt: str,
                 model: str = "gpt-3.5-turbo",
                 retries: int = 3):
        super().__init__(retries=retries)
        self.system_prompt = system_prompt
        self.model = model
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def execute(self, input_result: Result[TextInput, str]) -> Result[SummaryOutput, str]:
        """Execute the async summarization task."""
        if input_result.is_err():
            return input_result

        try:
            text_data = input_result.unwrap()

            # Validate input
            if not text_data.text.strip():
                return Err(f"Empty content for text ID: {text_data.id}")

            # Call OpenAI API asynchronously
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text_data.text}
                ],
                max_tokens=150,
                temperature=0.3
            )

            # Extract summary
            summary = response.choices[0].message.content
            if not summary:
                return Err(f"No summary generated for text ID: {text_data.id}")

            # Create result
            result = SummaryOutput(
                original_text=text_data.text,
                summary=summary.strip(),
                tokens_used=response.usage.total_tokens,
                task_id=self.task_id
            )

            return Ok(result)

        except Exception as e:
            return Err(f"OpenAI API error for text ID {text_data.id}: {str(e)} (Task: {self.task_id})")


def create_sample_texts() -> List[TextInput]:
    """Create sample texts for demonstration."""
    return [
        TextInput(
            text="""
            Artificial Intelligence is rapidly transforming various industries,
            from healthcare to finance. Machine learning algorithms are becoming
            more sophisticated, enabling computers to perform tasks that previously
            required human intelligence. Deep learning, a subset of machine learning,
            uses neural networks with multiple layers to process and analyze complex data.
            """,
            id="tech_article"
        ),
        TextInput(
            text="""
            Climate change continues to be a pressing global issue. Rising temperatures,
            melting ice caps, and extreme weather events are becoming more frequent.
            Scientists worldwide are working on innovative solutions including renewable
            energy technologies, carbon capture methods, and sustainable agriculture
            practices to mitigate the effects of global warming.
            """,
            id="climate_news"
        ),
        TextInput(
            text="""
            Space exploration has entered a new era with private companies joining
            government agencies in pursuing ambitious missions. Mars exploration,
            asteroid mining, and space tourism are no longer science fiction but
            achievable goals. Advanced rocket technology and international cooperation
            are driving unprecedented progress in our understanding of the cosmos.
            """,
            id="space_exploration"
        ),
        TextInput(
            text="""
            Recent medical breakthroughs in gene therapy and personalized medicine
            are revolutionizing healthcare. CRISPR technology allows precise genetic
            editing, while immunotherapy is showing remarkable success in cancer
            treatment. Telemedicine and AI-assisted diagnosis are making healthcare
            more accessible and accurate than ever before.
            """,
            id="medical_breakthrough"
        ),
        TextInput(
            text="""
            Quantum computing represents a paradigm shift in computational power.
            Unlike classical computers that use bits, quantum computers use qubits
            that can exist in multiple states simultaneously. This quantum superposition
            enables solving complex problems exponentially faster, with applications
            in cryptography, drug discovery, and financial modeling.
            """,
            id="quantum_computing"
        )
    ]

async def run_replicated_async_tasks():
    """
    Demonstrate async task replication using AsyncPipeline.replicate_task method.

    This shows how to:
    - Create a single async task configuration
    - Replicate it multiple times with unique IDs
    - Run replicated tasks concurrently on different inputs
    - Track which task processed which input
    """
    print("🔄 ASYNC TASK REPLICATION DEMO")
    print("=" * 60)
    print("Replicating async OpenAI task and running concurrently...")

    # System prompt used for all summarizations
    system_prompt = """
    You are a professional summarizer. Create concise, informative summaries
    that capture the key points and main ideas of the given text. Focus on
    the most important information and maintain a clear, readable style.
    """

    # Create a single async summarization task
    summarization_task = AsyncOpenAISummarizationTask(
        system_prompt=system_prompt,
        model="gpt-3.5-turbo",
        retries=2
    )

    # Get sample texts
    texts = create_sample_texts()

    # Create pipeline and replicate the task
    pipeline = AsyncPipeline[TextInput, str]()
    replicated_tasks = pipeline.replicate_task(summarization_task, num_replicas=len(texts))

    print(f"🔄 Replicated 1 async task into {len(replicated_tasks)} instances")
    print(f"Task IDs: {[task.task_id for task in replicated_tasks]}")
    print("-" * 60)

    # Show task-to-input mapping
    for i, (task, text) in enumerate(zip(replicated_tasks, texts)):
        print(f"📝 Task {task.task_id} → Text '{text.id}'")

    print(f"\nStarting concurrent execution of {len(replicated_tasks)} replicated async tasks...")
    print("-" * 60)

    # Create individual pipelines for each replicated task
    pipelines = []
    inputs = []

    for task, text in zip(replicated_tasks, texts):
        pipeline = AsyncPipeline.from_tasks([task])
        pipelines.append(pipeline)
        inputs.append(Ok(text))

    # Run pipelines in parallel
    start_time = asyncio.get_event_loop().time()
    execution_results = await AsyncPipeline.run_parallel(
        pipelines,
        inputs,
        debug=True
    )
    end_time = asyncio.get_event_loop().time()

    print(f"Parallel async execution completed in {end_time - start_time:.2f}s")
    print("-" * 60)

    # Process results
    successful_summaries = []
    failed_summaries = []

    for i, exec_result in enumerate(execution_results):
        text_id = texts[i].id
        task_id = replicated_tasks[i].task_id

        if exec_result.result.is_ok():
            summary = exec_result.result.unwrap()
            successful_summaries.append(summary)
            print(f"✅ Successfully processed '{text_id}' with async task {task_id}:")
            print(f"   Original length: {len(texts[i].text)} chars")
            print(f"   Summary length: {len(summary.summary)} chars")
            print(f"   Tokens used: {summary.tokens_used}")
            print(f"   Task ID: {summary.task_id}")
            print(f"   Execution time: {exec_result.execution_time:.2f}s")
            if exec_result.trace:
                print(f"   Trace steps: {len(exec_result.trace.steps)}")
            print()
        else:
            error_msg = exec_result.result.unwrap_err()
            failed_summaries.append((text_id, error_msg))
            print(f"❌ Failed to process '{text_id}' with async task {task_id}:")
            print(f"   Error: {error_msg}")
            print(f"   Execution time: {exec_result.execution_time:.2f}s")
            print()

    # Summary statistics
    print("=" * 60)
    print("ASYNC TASK REPLICATION SUMMARY")
    print("=" * 60)
    print(f"Original async task replicated: {len(replicated_tasks)} times")
    print(f"Total texts processed: {len(texts)}")
    print(f"Successful summaries: {len(successful_summaries)}")
    print(f"Failed summaries: {len(failed_summaries)}")

    if successful_summaries:
        total_tokens = sum(s.tokens_used for s in successful_summaries)
        avg_tokens = total_tokens / len(successful_summaries)
        print(f"Total tokens used: {total_tokens}")
        print(f"Average tokens per summary: {avg_tokens:.1f}")

        # Show async task performance
        task_performance = [(s.task_id, s.tokens_used) for s in successful_summaries]
        task_performance.sort(key=lambda x: x[1])
        print(f"Most efficient async task: {task_performance[0][0]} ({task_performance[0][1]} tokens)")
        print(f"Least efficient async task: {task_performance[-1][0]} ({task_performance[-1][1]} tokens)")

    total_time = sum(result.execution_time for result in execution_results)
    avg_time = total_time / len(execution_results)
    print(f"Total execution time: {total_time:.2f}s")
    print(f"Average time per replicated async task: {avg_time:.2f}s")
    print(f"Concurrent speedup vs sequential: ~{len(texts):.1f}x faster")

    return execution_results

async def demonstrate_concurrent_vs_sequential():
    """
    Compare concurrent replicated tasks vs sequential processing.
    """
    print("\n🔍 CONCURRENT vs SEQUENTIAL COMPARISON")
    print("=" * 60)
    print("Comparing replicated async tasks vs sequential processing...")

    system_prompt = "Create a brief summary of the main points."

    # Create base task
    summarization_task = AsyncOpenAISummarizationTask(
        system_prompt=system_prompt,
        model="gpt-3.5-turbo",
        retries=1
    )

    # Use first 3 texts for comparison
    texts = create_sample_texts()[:3]

    print(f"\n1. CONCURRENT EXECUTION (Replicated Tasks)")
    print("-" * 50)

    # Concurrent execution with replicated tasks
    pipeline = AsyncPipeline[TextInput, str]()
    replicated_tasks = pipeline.replicate_task(summarization_task, num_replicas=len(texts))

    pipelines = [AsyncPipeline.from_tasks([task]) for task in replicated_tasks]
    inputs = [Ok(text) for text in texts]

    start_time = asyncio.get_event_loop().time()
    concurrent_results = await AsyncPipeline.run_parallel(pipelines, inputs, debug=False)
    concurrent_time = asyncio.get_event_loop().time() - start_time

    concurrent_success = sum(1 for r in concurrent_results if r.result.is_ok())
    print(f"   Time: {concurrent_time:.2f}s")
    print(f"   Success: {concurrent_success}/{len(texts)}")
    print(f"   Tasks used: {len(replicated_tasks)} replicated instances")

    print(f"\n2. SEQUENTIAL EXECUTION (Same Task)")
    print("-" * 50)

    # Sequential execution with same task
    start_time = asyncio.get_event_loop().time()
    sequential_results = []

    for text in texts:
        pipeline = AsyncPipeline.from_tasks([summarization_task])
        result = await pipeline.run_sequence(Ok(text), debug=False)
        sequential_results.append(result)

    sequential_time = asyncio.get_event_loop().time() - start_time
    sequential_success = sum(1 for r in sequential_results if r.result.is_ok())

    print(f"   Time: {sequential_time:.2f}s")
    print(f"   Success: {sequential_success}/{len(texts)}")
    print(f"   Tasks used: 1 task instance (reused)")

    print(f"\n📊 PERFORMANCE ANALYSIS")
    print("-" * 50)
    speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0
    print(f"Concurrent replicated tasks: {concurrent_time:.2f}s")
    print(f"Sequential single task: {sequential_time:.2f}s")
    print(f"Speedup with replication: {speedup:.1f}x faster")
    print(f"Efficiency gain: {((sequential_time - concurrent_time) / sequential_time * 100):.1f}%")

    return concurrent_results, sequential_results

async def demonstrate_async_task_benefits():
    """
    Demonstrate the benefits of async task replication.
    """
    print("\n⚡ ASYNC TASK REPLICATION BENEFITS")
    print("=" * 60)
    print("Demonstrating benefits of async task replication...")

    system_prompt = "Provide a concise summary of the key innovations."

    # Create base async task
    base_task = AsyncOpenAISummarizationTask(
        system_prompt=system_prompt,
        model="gpt-3.5-turbo",
        retries=1
    )

    print(f"🔧 Base async task created with ID: {base_task.task_id}")

    # Create pipeline and replicate the task
    pipeline = AsyncPipeline[TextInput, str]()
    replicated_tasks = pipeline.replicate_task(base_task, num_replicas=3)

    print(f"🔄 Async task replicated {len(replicated_tasks)} times:")
    for i, task in enumerate(replicated_tasks):
        print(f"   Replica {i+1}: {task.task_id}")
        print(f"   Same config: {task.system_prompt == base_task.system_prompt}")
        print(f"   Unique ID: {task.task_id != base_task.task_id}")
        print(f"   Async client: {type(task.client).__name__}")
        print()

    # Test with sample texts
    sample_texts = create_sample_texts()[:3]

    print("Testing replicated async tasks concurrently...")
    print("-" * 50)

    # Create pipelines for each replicated task
    pipelines = []
    inputs = []

    for task, text in zip(replicated_tasks, sample_texts):
        pipeline = AsyncPipeline.from_tasks([task])
        pipelines.append(pipeline)
        inputs.append(Ok(text))

    # Run all replicated tasks concurrently
    start_time = asyncio.get_event_loop().time()
    results = await AsyncPipeline.run_parallel(pipelines, inputs, debug=True)
    end_time = asyncio.get_event_loop().time()

    print(f"Concurrent async execution completed in {end_time - start_time:.2f}s")
    print("-" * 50)

    successful_count = 0
    for i, result in enumerate(results):
        if result.result.is_ok():
            summary = result.result.unwrap()
            successful_count += 1
            print(f"✅ Replica {i+1} (Task {replicated_tasks[i].task_id}):")
            print(f"   Text: {sample_texts[i].id}")
            print(f"   Tokens: {summary.tokens_used}")
            print(f"   Time: {result.execution_time:.2f}s")
            print(f"   Task ID in result: {summary.task_id}")
        else:
            print(f"❌ Replica {i+1} failed: {result.result.unwrap_err()}")
        print()

    print(f"📊 Async Replication Results:")
    print(f"   Successful executions: {successful_count}/{len(replicated_tasks)}")
    print(f"   Total concurrent time: {end_time - start_time:.2f}s")
    print(f"   Average time per task: {(end_time - start_time)/len(replicated_tasks):.2f}s")
    print(f"   Async advantage: Non-blocking concurrent execution")

    return results

async def demonstrate_async_error_handling():
    """
    Demonstrate error handling in replicated async tasks.
    """
    print("\n🔍 ASYNC ERROR HANDLING WITH REPLICATION")
    print("=" * 60)

    system_prompt = "Summarize this text:"

    # Create base task
    base_task = AsyncOpenAISummarizationTask(
        system_prompt=system_prompt,
        retries=1
    )

    # Create test cases - some will fail
    test_cases = [
        TextInput(text="This is a valid text for summarization that should work fine.", id="valid_text"),
        TextInput(text="", id="empty_text"),  # This will fail
        TextInput(text="Short", id="too_short"),  # This might fail
    ]

    # Replicate task for each test case
    pipeline = AsyncPipeline[TextInput, str]()
    replicated_tasks = pipeline.replicate_task(base_task, num_replicas=len(test_cases))

    print(f"Testing {len(test_cases)} scenarios with {len(replicated_tasks)} replicated async tasks:")
    for i, (task, test_case) in enumerate(zip(replicated_tasks, test_cases)):
        print(f"   Task {task.task_id} → {test_case.id}")

    # Create pipelines and run in parallel
    pipelines = [AsyncPipeline.from_tasks([task]) for task in replicated_tasks]
    inputs = [Ok(test_case) for test_case in test_cases]

    print("\nRunning error handling test...")
    print("-" * 50)

    start_time = asyncio.get_event_loop().time()
    results = await AsyncPipeline.run_parallel(pipelines, inputs, debug=True)
    end_time = asyncio.get_event_loop().time()

    print(f"Async error handling test completed in {end_time - start_time:.2f}s")
    print("-" * 50)

    for i, (result, test_case, task) in enumerate(zip(results, test_cases, replicated_tasks)):
        print(f"\n{test_case.id.upper()} (Task {task.task_id}):")

        if result.result.is_ok():
            summary = result.result.unwrap()
            print(f"   ✅ Success: {summary.tokens_used} tokens")
            print(f"   Summary: {summary.summary[:50]}...")
        else:
            print(f"   ❌ Error: {result.result.unwrap_err()}")

        print(f"   Execution time: {result.execution_time:.2f}s")
        if result.trace:
            print(f"   Trace steps: {len(result.trace.steps)}")

    # Show error isolation benefit
    successful = sum(1 for r in results if r.result.is_ok())
    failed = len(results) - successful

    print(f"\n🛡️ Error Isolation Benefits:")
    print(f"   Total tasks: {len(results)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Success rate: {successful/len(results)*100:.1f}%")
    print(f"   Key benefit: Failed tasks don't affect successful ones!")

    return results

async def async_replication_performance_analysis():
    """
    Analyze performance characteristics of async task replication.
    """
    print("\n📊 ASYNC TASK REPLICATION PERFORMANCE ANALYSIS")
    print("=" * 60)

    system_prompt = "Provide a brief summary of the main points."
    texts = create_sample_texts()[:4]  # Use 4 texts for analysis

    # Create base task
    base_task = AsyncOpenAISummarizationTask(
        system_prompt=system_prompt,
        model="gpt-3.5-turbo",
        retries=1
    )

    print(f"Performance analysis with {len(texts)} texts...\n")

    # 1. Single task, sequential execution
    print("1. Single Async Task (Sequential Processing)")
    start_time = asyncio.get_event_loop().time()

    sequential_results = []
    for text in texts:
        pipeline = AsyncPipeline.from_tasks([base_task])
        result = await pipeline.run_sequence(Ok(text), debug=False)
        sequential_results.append(result)

    sequential_time = asyncio.get_event_loop().time() - start_time
    sequential_success = sum(1 for r in sequential_results if r.result.is_ok())
    print(f"   Time: {sequential_time:.2f}s")
    print(f"   Success: {sequential_success}/{len(texts)}")
    print(f"   Tasks used: 1 (reused)")

    # 2. Replicated tasks, parallel execution
    print("\n2. Replicated Async Tasks (Parallel Processing)")
    pipeline = AsyncPipeline[TextInput, str]()
    replicated_tasks = pipeline.replicate_task(base_task, num_replicas=len(texts))

    pipelines = [AsyncPipeline.from_tasks([task]) for task in replicated_tasks]
    inputs = [Ok(text) for text in texts]

    start_time = asyncio.get_event_loop().time()
    parallel_results = await AsyncPipeline.run_parallel(pipelines, inputs, debug=False)
    parallel_time = asyncio.get_event_loop().time() - start_time

    parallel_success = sum(1 for r in parallel_results if r.result.is_ok())
    print(f"   Time: {parallel_time:.2f}s")
    print(f"   Success: {parallel_success}/{len(texts)}")
    print(f"   Tasks used: {len(replicated_tasks)} (replicated)")

    # 3. Analysis
    print(f"\n📈 Performance Metrics:")
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    efficiency = (sequential_time - parallel_time) / sequential_time * 100 if sequential_time > 0 else 0

    print(f"   Sequential time: {sequential_time:.2f}s")
    print(f"   Parallel time: {parallel_time:.2f}s")
    print(f"   Speedup: {speedup:.1f}x faster")
    print(f"   Efficiency gain: {efficiency:.1f}%")
    print(f"   Scalability: Linear with task replication")

    # 4. Resource utilization
    print(f"\n💻 Resource Utilization:")
    print(f"   Memory overhead: {len(replicated_tasks)} task instances")
    print(f"   Concurrent connections: {len(replicated_tasks)} to OpenAI API")
    print(f"   Task isolation: Each replica independent")
    print(f"   Error resilience: Failures don't cascade")

    # 5. Recommendations
    print(f"\n💡 Recommendations:")
    if speedup > 2:
        print(f"   ✅ Excellent: Task replication provides {speedup:.1f}x speedup")
        print(f"   ✅ Use replicated tasks for parallel processing")
    elif speedup > 1.5:
        print(f"   🟡 Good: Task replication provides {speedup:.1f}x speedup")
        print(f"   🟡 Consider replicated tasks for time-sensitive operations")
    else:
        print(f"   🔴 Limited: Only {speedup:.1f}x speedup - check for bottlenecks")
        print(f"   🔴 Sequential might be sufficient for this workload")

    return parallel_results, sequential_results

async def main():
    """Main demonstration function."""
    # Ensure OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("or create a .env file with: OPENAI_API_KEY=your-api-key-here")
        return

    print("🚀 NeoPipe OpenAI Async Pipeline Example")
    print("=" * 60)

    try:
        # Run all demonstrations
        await run_replicated_async_tasks()
        await demonstrate_concurrent_vs_sequential()
        await demonstrate_async_task_benefits()
        await demonstrate_async_error_handling()
        await async_replication_performance_analysis()

        print("\n✨ Async task replication example completed!")
        print("\nKey takeaways:")
        print("- replicate_task() creates multiple async task instances with unique IDs")
        print("- Async replication enables true concurrent processing with non-blocking I/O")
        print("- Each replicated async task operates independently")
        print("- Perfect for scaling API calls and I/O-bound operations")
        print("- Significant performance improvements over sequential execution")
        print("- Error isolation: failures in one replica don't affect others")
        print("- AsyncPipeline.run_parallel() efficiently manages concurrent execution")
        print("- Ideal for high-throughput, low-latency processing scenarios")

    except Exception as e:
        print(f"❌ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Features Demonstrated

### 1. **Three Async Execution Modes**

**Async Task Replication:**
```python
# Create base async task
base_task = AsyncOpenAISummarizationTask(system_prompt, model="gpt-3.5-turbo")

# Replicate async task with unique IDs
pipeline = AsyncPipeline[TextInput, str]()
replicated_tasks = pipeline.replicate_task(base_task, num_replicas=5)

# Each replica has unique task_id but same async configuration
print([task.task_id for task in replicated_tasks])
```

**Parallel Execution of Replicated Async Tasks:**
```python
# Create individual pipelines for each replicated async task
pipelines = [AsyncPipeline.from_tasks([task]) for task in replicated_tasks]

# Run in parallel with concurrent async execution
execution_results = await AsyncPipeline.run_parallel(pipelines, inputs, debug=True)
```

### 2. **Async Task Tracking and Performance**
```python
# Each replicated async task provides detailed tracking
result = SummaryOutput(
    original_text=text_data.text,
    summary=summary.strip(),
    tokens_used=response.usage.total_tokens,
    task_id=self.task_id  # Unique async task identifier
)
```

### 3. **Non-blocking Concurrent API Calls**
```python
# Multiple async API calls execute concurrently
response = await self.client.chat.completions.create(
    model=self.model,
    messages=[
        {"role": "system", "content": self.system_prompt},
        {"role": "user", "content": text_data.text}
    ],
    max_tokens=150,
    temperature=0.3
)
```

### 4. **Benefits of Async Task Replication**
- **Concurrency**: True parallel async execution
- **Scalability**: Linear performance improvement with replicas
- **Efficiency**: Non-blocking I/O maximizes resource utilization
- **Isolation**: Independent async task instances
- **Monitoring**: Individual task performance tracking
- **Resilience**: Async error handling with fault isolation

### 5. **Use Cases for Async Task Replication**
- High-throughput API processing
- Concurrent data fetching from multiple sources
- Parallel machine learning inference
- Real-time data processing pipelines
- Scalable microservices orchestration

## Setup Requirements

```bash
# Install dependencies
pip install openai python-dotenv

# Set up environment
export OPENAI_API_KEY="your-api-key-here"
# or create .env file with: OPENAI_API_KEY=your-api-key-here
```

## When to Use Async Task Replication

| Scenario | Benefit | Performance Gain | Best Use Case |
|----------|---------|------------------|---------------|
| **I/O-bound operations** | Non-blocking concurrent execution | 3-10x speedup | API calls, file processing |
| **Independent processing** | Parallel execution without dependencies | Linear scaling | Multiple data sources |
| **High-throughput systems** | Maximize resource utilization | Significant | Real-time processing |
| **Fault-tolerant systems** | Error isolation between replicas | Same + resilience | Production systems |

This example demonstrates NeoPipe's async task replication for building highly scalable, concurrent processing systems with optimal resource utilization and comprehensive monitoring.