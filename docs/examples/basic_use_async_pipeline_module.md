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

---

## 4. Notes

- **1:1 matching**: The `inputs` list must be the same length as your `tasks` list.  
- **Short‑circuit**: The first `Err` stops the entire pipeline (unless you inspect partial trace).  
- **Retries**: Any task annotated with `retries > 1` will automatically retry on exceptions.  
- **Trace**: In `debug` mode you get a list of `(task_name, Result)` in the order tasks were run.
