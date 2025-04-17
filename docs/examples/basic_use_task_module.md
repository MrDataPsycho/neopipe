# Task Module

The **Sync Task** system provides a uniform, retryable wrapper around functions and classes that operate on `Result[T, E]`. Instead of raising exceptions, every task consumes a `Result` and returns a new `Result`, enabling safe, composable pipelines.

---

## Overview

- **BaseSyncTask**  
  Abstract base that handles:
  - Retry with exponential backoff  
  - Task identification (`task_id`, `task_name`)  
  - Logging on attempts, success, and failure  

## FunctionSyncTask
  Decorator wrapper for free functions:
  ```python
  @FunctionSyncTask.decorator(retries=2)
  def my_task(res: Result[int, str]) -> Result[int, str]:
      if res.is_ok():
          return Ok(res.unwrap() + 1)
      return res
```

## ClassSyncTask
Subclass for stateful or multi‑step logic:

```python
class MultiplyTask(ClassSyncTask[int, str]):
    def __init__(self, multiplier: int):
        super().__init__(retries=3)
        self.multiplier = multiplier

    def execute(self, res: Result[int, str]) -> Result[int, str]:
        if res.is_ok():
            return Ok(res.unwrap() * self.multiplier)
        return res

```

# BaseSyncTask
```python
from neopipe.task import BaseSyncTask
from neopipe.result import Result, Ok, Err

class EchoTask(BaseSyncTask[str, str]):
    def execute(self, res: Result[str, str]) -> Result[str, str]:
        return Ok(res.unwrap()) if res.is_ok() else res

task = EchoTask()
print(task(Ok("hello")))  # Ok("hello")

```

# FunctionSyncTask
```python
from neopipe.task import FunctionSyncTask
from neopipe.result import Result, Ok, Err

@FunctionSyncTask.decorator(retries=2)
def add_ten(res: Result[int, str]) -> Result[int, str]:
    if res.is_ok():
        return Ok(res.unwrap() + 10)
    return res

print(add_ten(Ok(5)))  # Ok(15)
```

## ClassSyncTask
```python

from neopipe.task import ClassSyncTask
from neopipe.result import Result, Ok

class SquareTask(ClassSyncTask[int, str]):
    def execute(self, res: Result[int, str]) -> Result[int, str]:
        if res.is_ok():
            return Ok(res.unwrap() ** 2)
        return res

task = SquareTask()
print(task(Ok(3)))  # Ok(9)
```

Read the Pipeline Basics to see how to chain Sync Tasks.


# FunctionAsyncTask

```python
from neopipe.async_task import FunctionAsyncTask
from neopipe.result import Result, Ok, Err

@FunctionAsyncTask.decorator(retries=2)
async def shout(res: Result[str, str]) -> Result[str, str]:
    if res.is_ok():
        return Ok(res.unwrap().upper())
    return res

print(await shout(Ok("hello")))  # Ok("HELLO")

```

# ClassAsyncTask
```python
from neopipe.async_task import ClassAsyncTask
from neopipe.result import Result, Ok

class ReverseTask(ClassAsyncTask[str, str]):
    async def execute(self, res: Result[str, str]) -> Result[str, str]:
        if res.is_ok():
            return Ok(res.unwrap()[::-1])
        return res

task = ReverseTask()
print(await task(Ok("abc")))  # Ok("cba")
```