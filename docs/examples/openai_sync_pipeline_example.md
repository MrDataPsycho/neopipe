# OpenAI Sync Pipeline with Task Replication Example

This example demonstrates using NeoPipe's `replicate_task` method to create multiple instances of the same OpenAI task and run them in parallel using SyncPipeline.

## Overview

We'll create an OpenAI summarization system that:
- Uses a single OpenAI task configuration
- Replicates the task 5 times using `replicate_task` method
- Runs replicated tasks in parallel on different texts
- Demonstrates the power of task replication for scaling
- Shows proper error handling with Result types

## Complete Example

```python
import os
from typing import List, Dict, Any
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

from neopipe import Result, Ok, Err
from neopipe.task import ClassSyncTask
from neopipe.pipeline import SyncPipeline

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

class OpenAISummarizationTask(ClassSyncTask[TextInput, str]):
    """
    A task that calls OpenAI API to summarize text using a consistent system prompt.

    This demonstrates:
    - Class-based task configuration
    - External API integration
    - Comprehensive error handling
    - Result type usage
    """

    def __init__(self,
                 system_prompt: str,
                 model: str = "gpt-3.5-turbo",
                 retries: int = 3):
        super().__init__(retries=retries)
        self.system_prompt = system_prompt
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def execute(self, input_result: Result[TextInput, str]) -> Result[SummaryOutput, str]:
        """Execute the summarization task."""
        if input_result.is_err():
            return input_result

        try:
            text_data = input_result.unwrap()

            # Validate input
            if not text_data.text.strip():
                return Err(f"Empty content for text ID: {text_data.id}")

            # Call OpenAI API
            response = self.client.chat.completions.create(
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

def run_replicated_task_demo():
    """
    Demonstrate task replication using SyncPipeline.replicate_task method.

    This shows how to:
    - Create a single task configuration
    - Replicate it multiple times with unique IDs
    - Run replicated tasks in parallel
    - Track which task processed which input
    """

    # System prompt used for all summarizations
    system_prompt = """
    You are a professional summarizer. Create concise, informative summaries
    that capture the key points and main ideas of the given text. Focus on
    the most important information and maintain a clear, readable style.
    """

    # Create sample texts
    texts = create_sample_texts()

    # Create a single summarization task
    summarization_task = OpenAISummarizationTask(
        system_prompt=system_prompt,
        model="gpt-3.5-turbo",
        retries=2
    )

    # Create a pipeline and replicate the task 5 times
    pipeline = SyncPipeline[TextInput, str]()
    replicated_tasks = pipeline.replicate_task(summarization_task, num_replicas=5)

    print(f"🔄 Replicated 1 task into {len(replicated_tasks)} instances")
    print(f"Task IDs: {[task.task_id for task in replicated_tasks]}")
    print("-" * 60)

    # Create individual pipelines for each replicated task
    pipelines = []
    initial_inputs = []

    for i, (task, text) in enumerate(zip(replicated_tasks, texts)):
        # Each pipeline contains one replicated task
        pipeline = SyncPipeline.from_tasks([task])
        pipelines.append(pipeline)
        initial_inputs.append(Ok(text))
        print(f"📝 Pipeline {i+1}: Task {task.task_id} → Text '{text.id}'")

    print(f"\nStarting parallel execution of {len(replicated_tasks)} replicated tasks...")
    print("-" * 60)

    # Run pipelines in parallel
    try:
        # SyncPipeline.run_parallel executes multiple pipelines concurrently
        execution_results = SyncPipeline.run_parallel(
            pipelines,
            initial_inputs,
            debug=True  # Enable tracing for debugging
        )

        # Process results
        successful_summaries = []
        failed_summaries = []

        for i, exec_result in enumerate(execution_results):
            text_id = texts[i].id
            task_id = replicated_tasks[i].task_id

            if exec_result.result.is_ok():
                summary = exec_result.result.unwrap()
                successful_summaries.append(summary)

                print(f"✅ Successfully processed '{text_id}' with task {task_id}:")
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

                print(f"❌ Failed to process '{text_id}' with task {task_id}:")
                print(f"   Error: {error_msg}")
                print(f"   Execution time: {exec_result.execution_time:.2f}s")
                print()

        # Summary statistics
        print("=" * 60)
        print("TASK REPLICATION SUMMARY")
        print("=" * 60)
        print(f"Original task replicated: {len(replicated_tasks)} times")
        print(f"Total texts processed: {len(texts)}")
        print(f"Successful summaries: {len(successful_summaries)}")
        print(f"Failed summaries: {len(failed_summaries)}")

        if successful_summaries:
            total_tokens = sum(s.tokens_used for s in successful_summaries)
            avg_tokens = total_tokens / len(successful_summaries)
            print(f"Total tokens used: {total_tokens}")
            print(f"Average tokens per summary: {avg_tokens:.1f}")

            # Show which tasks were most/least efficient
            task_performance = [(s.task_id, s.tokens_used) for s in successful_summaries]
            task_performance.sort(key=lambda x: x[1])
            print(f"Most efficient task: {task_performance[0][0]} ({task_performance[0][1]} tokens)")
            print(f"Least efficient task: {task_performance[-1][0]} ({task_performance[-1][1]} tokens)")

        total_time = sum(result.execution_time for result in execution_results)
        print(f"Total execution time: {total_time:.2f}s")
        print(f"Average time per replicated task: {total_time/len(execution_results):.2f}s")

        # Display actual summaries
        if successful_summaries:
            print("\n" + "=" * 60)
            print("SUMMARIES BY REPLICATED TASKS")
            print("=" * 60)

            for i, summary in enumerate(successful_summaries):
                print(f"\n📝 TEXT: {texts[i].id.upper()} | TASK: {summary.task_id}")
                print("-" * 50)
                print(summary.summary)
                print(f"(Tokens: {summary.tokens_used})")

        return execution_results

    except Exception as e:
        print(f"❌ Pipeline execution failed: {str(e)}")
        return None

def demonstrate_task_replication_benefits():
    """
    Demonstrate the benefits and use cases of task replication.
    """
    print("\n" + "=" * 60)
    print("TASK REPLICATION BENEFITS DEMONSTRATION")
    print("=" * 60)

    system_prompt = "Summarize the following text:"

    # Create base task
    base_task = OpenAISummarizationTask(
        system_prompt=system_prompt,
        retries=1
    )

    print(f"🔧 Base task created with ID: {base_task.task_id}")

    # Create pipeline and replicate the task
    pipeline = SyncPipeline[TextInput, str]()
    replicated_tasks = pipeline.replicate_task(base_task, num_replicas=3)

    print(f"🔄 Task replicated {len(replicated_tasks)} times:")
    for i, task in enumerate(replicated_tasks):
        print(f"   Replica {i+1}: {task.task_id}")
        print(f"   Same config: {task.system_prompt == base_task.system_prompt}")
        print(f"   Unique ID: {task.task_id != base_task.task_id}")
        print()

    # Test with sample text
    sample_text = TextInput(
        text="Task replication allows scaling the same operation across multiple inputs efficiently.",
        id="replication_demo"
    )

    print("Testing replicated tasks with same input...")

    for i, task in enumerate(replicated_tasks[:2]):  # Test first 2 replicas
        pipeline = SyncPipeline.from_tasks([task])
        result = pipeline.run(Ok(sample_text), debug=True)

        if result.result.is_ok():
            summary = result.result.unwrap()
            print(f"✅ Replica {i+1} (Task {task.task_id}):")
            print(f"   Tokens: {summary.tokens_used}")
            print(f"   Time: {result.execution_time:.2f}s")
        else:
            print(f"❌ Replica {i+1} failed: {result.result.unwrap_err()}")

if __name__ == "__main__":
    # Ensure OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("or create a .env file with: OPENAI_API_KEY=your-api-key-here")
        exit(1)

    print("🚀 NeoPipe OpenAI Sync Pipeline Example")
    print("=" * 60)

    # Run the main demonstration
    results = run_replicated_task_demo()

    # Demonstrate task replication benefits
    demonstrate_task_replication_benefits()

    print("\n✨ Task replication example completed!")
    print("\nKey takeaways:")
    print("- replicate_task() creates multiple instances with unique IDs")
    print("- Replicated tasks share configuration but have independent execution")
    print("- Perfect for scaling identical operations across multiple inputs")
    print("- Each replica can be tracked and monitored separately")
    print("- Enables efficient parallel processing with minimal setup")
    print("- SyncPipeline.run_parallel handles concurrent execution seamlessly")
```

## Key Features Demonstrated

### 1. **Task Replication**
```python
# Create base task
summarization_task = OpenAISummarizationTask(system_prompt, model="gpt-3.5-turbo")

# Replicate task 5 times with unique IDs
pipeline = SyncPipeline[TextInput, str]()
replicated_tasks = pipeline.replicate_task(summarization_task, num_replicas=5)

# Each replica has unique task_id but same configuration
print([task.task_id for task in replicated_tasks])
```

### 2. **Parallel Execution of Replicated Tasks**
```python
# Create individual pipelines for each replicated task
pipelines = [SyncPipeline.from_tasks([task]) for task in replicated_tasks]

# Run in parallel with different inputs
execution_results = SyncPipeline.run_parallel(pipelines, inputs, debug=True)
```

### 3. **Task Tracking and Identification**
```python
# Each replicated task has unique ID for tracking
result = SummaryOutput(
    original_text=text_data.text,
    summary=summary.strip(),
    tokens_used=response.usage.total_tokens,
    task_id=self.task_id  # Unique task identifier
)
```

### 4. **Benefits of Task Replication**
- **Scalability**: Easily scale identical operations
- **Traceability**: Track which task processed which input
- **Resource Management**: Independent task instances
- **Fault Isolation**: Failures in one replica don't affect others
- **Performance Monitoring**: Compare efficiency across replicas

### 5. **Use Cases for Task Replication**
- Processing multiple similar inputs with same logic
- A/B testing different configurations
- Load balancing across task instances
- Parallel processing of independent data sets
- Scaling API calls efficiently

## Setup Requirements

To run this example, you'll need:

```bash
# Install dependencies
pip install openai python-dotenv

# Set up environment
export OPENAI_API_KEY="your-api-key-here"
# or create .env file with: OPENAI_API_KEY=your-api-key-here
```

## Expected Output

The example will show:
- Creation of 5 replicated tasks from a single base task
- Parallel processing with unique task identification
- Task performance comparison across replicas
- Generated summaries with task traceability
- Benefits of task replication for scaling

This demonstrates NeoPipe's `replicate_task` method for efficiently scaling identical operations across multiple inputs with full traceability and monitoring.