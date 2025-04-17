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

You can also run two pipelines in parallel and merge their outputs.

```python
# Pipeline A: load & filter active
p1 = SyncPipeline.from_tasks([load_users, filter_active], name="LoadFilter")

# Pipeline B: load & extract names
@FunctionSyncTask.decorator()
def extract_ids(res: Result[list[dict], str]) -> Result[list[int], str]:
    return Ok([u["id"] for u in res.unwrap()]) if res.is_ok() else res

p2 = SyncPipeline.from_tasks([load_users, extract_ids], name="LoadIDs")

# Run in parallel
parallel = SyncPipeline.run_parallel(
    pipelines=[p1, p2],
    inputs=[Ok(None), Ok(None)]
)

if parallel.is_ok():
    active_users, user_ids = parallel.unwrap()
    print("Active users:", active_users)
    print("User IDs:", user_ids)
else:
    print("Parallel pipelines failed:", parallel.err())
```