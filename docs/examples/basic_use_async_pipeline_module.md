# Async Pipeline — Basic Usage

The **AsyncPipeline** lets you run independent `BaseAsyncTask` instances concurrently—1:1 matching each task with its input `Result`. You can also capture a full execution trace by enabling `debug` mode.

---

## Installation

```bash
pip install neopipe
```

---

## Imports

```python
import asyncio
from neopipe.result import Result, Ok, Err
from neopipe.async_task import FunctionAsyncTask, ClassAsyncTask
from neopipe.async_pipeline import AsyncPipeline
```

---

## 1. Define Your Async Tasks

### 1.1 Function‑based Tasks

```python
@FunctionAsyncTask.decorator(retries=2)
async def fetch_user(res: Result[int, str]) -> Result[dict, str]:
    # Simulate an async I/O call
    if res.is_ok():
        await asyncio.sleep(0.1)
        user_id = res.unwrap()
        return Ok({"id": user_id, "name": f"User{user_id}"})
    return res
```

```python
@FunctionAsyncTask.decorator()
async def validate_user(res: Result[dict, str]) -> Result[dict, str]:
    if res.is_ok():
        user = res.unwrap()
        if not user["id"] or not user["name"]:
            return Err("Invalid user data")
        return Ok(user)
    return res
```

### 1.2 Class‑based Tasks

```python
class EnrichUserTask(ClassAsyncTask[dict, str]):
    async def execute(self, res: Result[dict, str]) -> Result[dict, str]:
        if res.is_ok():
            user = res.unwrap()
            # add some computed field
            user["active"] = (user["id"] % 2 == 0)
            return Ok(user)
        return res
```

---

## 2. Build the Pipeline

```python
pipeline = AsyncPipeline.from_tasks([
    fetch_user,
    validate_user,
    EnrichUserTask()
], name="UserPipeline")
```

---

## 3. Run the Pipeline

### 3.1 Simple Concurrent Run

```python
async def main():
    inputs = [Ok(1), Ok(2), Ok(3)]  # three independent runs
    result = await pipeline.run(inputs)

    if result.is_ok():
        users = result.unwrap()
        print("Enriched users:", users)
    else:
        print("Pipeline failed:", result.err())

asyncio.run(main())
```

**Expected Output:**

```
Enriched users: [
  {"id":1,"name":"User1","active":False},
  {"id":2,"name":"User2","active":True},
  {"id":3,"name":"User3","active":False}
]
```

### 3.2 Debug Mode (Trace)

```python
async def debug_main():
    inputs = [Ok(10), Ok(20)]
    debug_result = await pipeline.run(inputs, debug=True)

    if debug_result.is_ok():
        outputs, trace = debug_result.unwrap()
        print("Final outputs:", outputs)
        print("Trace details:")
        for task_name, task_res in trace:
            print(f" - {task_name}: {task_res}")
    else:
        print("Pipeline error:", debug_result.err())

asyncio.run(debug_main())
```
## 4. Async Pipeline Parallel Execution

You can run multiple **`AsyncPipeline`** instances concurrently with `run_parallel()`. Each pipeline executes its sequence of tasks (via `run_sequence`) with its own input, and you get back a list of `PipelineResult` objects—and, in debug mode, a full `PipelineTrace`.

---

### 4.1. Define your pipelines

```python
import asyncio
from neopipe.result import Result, Ok, Err
from neopipe.async_task import FunctionAsyncTask, ClassAsyncTask
from neopipe.async_pipeline import AsyncPipeline

# — Sequential pipeline: load → filter → extract names
@FunctionAsyncTask.decorator()
async def load_users(res: Result[None, str]) -> Result[list[dict], str]:
    return Ok([
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob",   "active": False},
        {"id": 3, "name": "Carol", "active": True},
    ])

@FunctionAsyncTask.decorator()
async def filter_active(res: Result[list[dict], str]) -> Result[list[dict], str]:
    if res.is_err():
        return res
    return Ok([u for u in res.unwrap() if u["active"]])

class ExtractNamesTask(ClassAsyncTask[list[dict], str]):
    async def execute(self, res: Result[list[dict], str]) -> Result[list[str], str]:
        if res.is_err():
            return res
        return Ok([u["name"] for u in res.unwrap()])

seq_pipeline = AsyncPipeline.from_tasks(
    [load_users, filter_active, ExtractNamesTask()],
    name="UserSeq"
)

# — Independent pipelines: fetch and validate
@FunctionAsyncTask.decorator()
async def fetch_user(res: Result[int, str]) -> Result[dict, str]:
    if res.is_ok():
        await asyncio.sleep(0.05)
        uid = res.unwrap()
        return Ok({"id": uid, "name": f"User{uid}"})
    return res

@FunctionAsyncTask.decorator()
async def validate_user(res: Result[dict, str]) -> Result[dict, str]:
    if res.is_ok():
        user = res.unwrap()
        if not user.get("id") or not user.get("name"):
            return Err("Invalid")
        return Ok(user)
    return res

fetch_pipeline    = AsyncPipeline.from_tasks([fetch_user],    name="FetchUser")
validate_pipeline = AsyncPipeline.from_tasks([validate_user], name="ValidateUser")
```

### 4.2. Run the pipelines in parallel

```python
async def main():
    inputs = [
        Ok(None),                  # seq_pipeline: needs None
        Ok(42),                    # fetch_pipeline: user ID
        Ok({"id": 99, "name": "X"})# validate_pipeline: user dict
    ]

    # debug=False ⇒ Ok[List[PipelineResult]]
    res = await AsyncPipeline.run_parallel(
        [seq_pipeline, fetch_pipeline, validate_pipeline],
        inputs
    )

    if res.is_ok():
        for pr in res.unwrap():
            print(f"{pr.name} → {pr.result}")
    else:
        print("Error:", res.err())

asyncio.run(main())

```

Expected Output:

```
UserSeq      → ['Alice', 'Carol']
FetchUser    → {'id':42, 'name':'User42'}
ValidateUser → {'id':99, 'name':'X'}
```

### 4.3. Run the pipelines in parallel (debug mode)

```python
async def debug_main():
    inputs = [Ok(None), Ok(7), Ok({"id":7,"name":"User7"})]

    # debug=True ⇒ Ok((List[PipelineResult], PipelineTrace))
    res = await AsyncPipeline.run_parallel(
        [seq_pipeline, fetch_pipeline, validate_pipeline],
        inputs,
        debug=True
    )

    if res.is_ok():
        results, trace = res.unwrap()

        # Print final results
        for pr in results:
            print(f"{pr.name} → {pr.result}")

        # Print per-pipeline, per-task trace
        for single in trace.pipelines:
            print(f"\nTrace for {single.name}:")
            for task_name, task_res in single.tasks:
                print(f"  {task_name} → {task_res}")
    else:
        print("Error:", res.err())

asyncio.run(debug_main())
```
Expected Output:

```
UserSeq      → ['Alice', 'Carol']
FetchUser    → {'id':7, 'name':'User7'}
ValidateUser → {'id':7, 'name':'User7'}

Trace for UserSeq:
  load_users       → Ok([...])
  filter_active    → Ok([...])
  ExtractNamesTask → Ok(['Alice','Carol'])

Trace for FetchUser:
  fetch_user       → Ok({'id':7,'name':'User7'})

Trace for ValidateUser:
  validate_user    → Ok({'id':7,'name':'User7'})
```
---

## 5. Notes

- **1:1 matching**: The `inputs` list must be the same length as your `tasks` list.  
- **Short‑circuit**: The first `Err` stops the entire pipeline (unless you inspect partial trace).  
- **Retries**: Any task annotated with `retries > 1` will automatically retry on exceptions.  
- **Trace**: In `debug` mode you get a list of `(task_name, Result)` in the order tasks were run.
