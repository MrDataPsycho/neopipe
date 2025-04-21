# Basic Usage: Sync Pipeline

The **Sync Pipeline** ties together multiple `BaseSyncTask` instances—both function‑based and class‑based—into a single, sequential workflow. Each task consumes a `Result[T, E]` and returns a new `Result[U, E]`. The pipeline stops on the first failure and can optionally emit a full trace for debugging.

---

## Installation

```bash
pip install neopipe
```

---

## Imports

```python
from neopipe.result import Result, Ok, Err
from neopipe.task import FunctionSyncTask, ClassSyncTask
from neopipe.sync_pipeline import SyncPipeline
```

---

## 1. Define Your Tasks

### 1.1 Function‑based Tasks

```python
@FunctionSyncTask.decorator(retries=2)
def load_users(res: Result[None, str]) -> Result[list[dict], str]:
    # Simulate loading from a database
    return Ok([
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob",   "active": False},
        {"id": 3, "name": "Carol", "active": True},
    ])
```

```python
@FunctionSyncTask.decorator()
def filter_active(res: Result[list[dict], str]) -> Result[list[dict], str]:
    if res.is_err():
        return res
    active = [u for u in res.unwrap() if u["active"]]
    return Ok(active)
```

### 1.2 Class‑based Tasks

```python
class ExtractNamesTask(ClassSyncTask[list[dict], str]):
    def execute(self, res: Result[list[dict], str]) -> Result[list[str], str]:
        if res.is_err():
            return res
        names = [u["name"] for u in res.unwrap()]
        return Ok(names)
```

```python
class JoinNamesTask(ClassSyncTask[list[str], str]):
    def execute(self, res: Result[list[str], str]) -> Result[str, str]:
        if res.is_err():
            return res
        return Ok(", ".join(res.unwrap()))
```

---

## 2. Build the Pipeline

```python
pipeline = SyncPipeline.from_tasks([
    load_users,
    filter_active,
    ExtractNamesTask(),
    JoinNamesTask()
], name="UserNamePipeline")
```

---

## 3. Run the Pipeline

### 3.1 Simple Run

```python
result = pipeline.run(Ok(None))

if result.is_ok():
    print("Final output:", result.unwrap())
else:
    print("Pipeline failed:", result.err())
```

**Expected Output:**

```
Final output: Alice, Carol
```

### 3.2 Debug Mode (Trace)

```python
debug_result = pipeline.run(Ok(None), debug=True)

if debug_result.is_ok():
    final, trace = debug_result.unwrap()
    print("Final:", final)
    print("Trace:")
    for task_name, step_res in trace:
        print(f"  - {task_name}: {step_res}")
else:
    print("Pipeline failed:", debug_result.err())
```

**Sample Trace:**

```
Final: Alice, Carol
Trace:
  - load_users: Ok([{'id':1,...}, ...])
  - filter_active: Ok([{'id':1,...}, {'id':3,...}])
  - ExtractNamesTask: Ok(['Alice','Carol'])
  - JoinNamesTask: Ok('Alice, Carol')
```

---

## 4. Chaining Pipelines in Parallel


You can execute multiple `SyncPipeline` instances concurrently with `run_parallel`. Each pipeline runs in its own thread and returns a list of `PipelineResult` objects (and, in debug mode, a `PipelineTrace` with per‑task details).

---

### 4.1 Define your pipelines

```python
from neopipe.result import Result, Ok
from neopipe.task import FunctionSyncTask, ClassSyncTask
from neopipe.sync_pipeline import SyncPipeline

@FunctionSyncTask.decorator()
def compute_length(res: Result[str, str]) -> Result[int, str]:
    # returns the length of the string
    return Ok(len(res.unwrap())) if res.is_ok() else res

class MultiplyTask(ClassSyncTask[int, str]):
    def __init__(self, factor: int):
        super().__init__()
        self.factor = factor

    def execute(self, res: Result[int, str]) -> Result[int, str]:
        # multiplies the integer by the given factor
        return Ok(res.unwrap() * self.factor) if res.is_ok() else res

# Pipeline A: compute length → multiply by 2
pA = SyncPipeline.from_tasks(
    [compute_length, MultiplyTask(2)],
    name="LengthX2"
)

# Pipeline B: compute length → multiply by 3
pB = SyncPipeline.from_tasks(
    [compute_length, MultiplyTask(3)],
    name="LengthX3"
)
```

### 4.2 Run in parallel (non‑debug)
You can run the pipelines in parallel by passing a list of inputs, one for each pipeline:

```python
inputs = [Ok("hello"), Ok("world!")]  # one input per pipeline

result = SyncPipeline.run_parallel([pA, pB], inputs)

if result.is_ok():
    pipeline_results = result.unwrap()
    # pipeline_results is a List[PipelineResult]:
    # [
    #   PipelineResult(name="LengthX2", result=10),
    #   PipelineResult(name="LengthX3", result=18)
    # ]
    for pr in pipeline_results:
        print(f"{pr.name} → {pr.result}")
else:
    print("Error:", result.err())
```

### 4.3 Run in parallel (debug mode)

Capture a full per‑task trace alongside the final results:

```python
res_debug = SyncPipeline.run_parallel([pA, pB], inputs, debug=True)

if res_debug.is_ok():
    pipeline_results, trace = res_debug.unwrap()
    
    # pipeline_results same as above
    # trace is a PipelineTrace(pipelines=[SinglePipelineTrace(...), ...])
    
    # Print results
    for pr in pipeline_results:
        print(f"{pr.name} final → {pr.result}")

    # Inspect per‑task trace
    for single in trace.pipelines:
        print(f"\nTrace for {single.name}:")
        for task_name, task_res in single.tasks:
            print(f"  {task_name} → {task_res}")
else:
    print("Error:", res_debug.err())
```

