# 🧰 Basic Usage: Tasks as Functions and Classes

The Task system lets you define **reliable, retryable units of work**. Tasks are always wrapped in a standardized structure that returns a `Result[T, E]` instead of throwing exceptions.

This ensures predictable control flow and composability — ideal for pipelines and automated workflows.

---

## ✅ Sync Function-Based Task

Use `FunctionSyncTask.decorator(...)` to turn a plain function into a task with retries and error handling.

```python
from result import Result, Ok, Err
from sync_task import FunctionSyncTask

@FunctionSyncTask.decorator(retries=2)
def double(x: int) -> Result[int, str]:
    if x < 0:
        return Err("Negative not allowed")
    return Ok(x * 2)

result = double(5)  # Ok(10)
```

✅ Sync Class-Based Task

Extend ClassSyncTask and implement execute():

```python
from result import Result, Ok
from sync_task import ClassSyncTask

class AddFiveTask(ClassSyncTask[int, str]):
    def __init__(self, x: int):
        super().__init__(retries=2)
        self.x = x

    def execute(self) -> Result[int, str]:
        return Ok(self.x + 5)

task = AddFiveTask(10)
result = task()  # Ok(15)
```

## ✅ Async Function-Based Task
Use `FunctionAsyncTask.decorator(...)` to turn a plain async function into a task with retries and error handling.

```python
from result import Result, Ok, Err
from async_task import FunctionAsyncTask

@FunctionAsyncTask.decorator(retries=3)
async def fetch(x: int) -> Result[str, str]:
    if x == 0:
        return Err("Bad input")
    return Ok(f"Data-{x}")

result = await fetch(42)  # Ok("Data-42")
```

## ✅ Async Class-Based Task

Extend ClassAsyncTask and implement execute():

```python
from result import Result, Ok
from async_task import ClassAsyncTask

class MultiplyAsyncTask(ClassAsyncTask[int, str]):
    def __init__(self, val: int):
        super().__init__(retries=2)
        self.val = val

    async def execute(self) -> Result[int, str]:
        return Ok(self.val * 10)

task = MultiplyAsyncTask(3)
result = await task()  # Ok(30)
```
