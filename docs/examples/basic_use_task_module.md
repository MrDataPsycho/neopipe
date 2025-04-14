# Task Module — Usage Examples

The `Task` module provides a robust way to wrap both **synchronous** and **asynchronous** computations with:
- ✅ Automatic retry logic
- ✅ Consistent `Result[Ok, Err]` handling
- ✅ Functional and object-oriented patterns
- ✅ Support for structured AI workflows (e.g., OpenAI SDK)

---

## 🔍 Use Case

We want to analyze a piece of text and extract structured data such as:
- Title
- Tags
- Summary

We'll simulate calling the OpenAI SDK to generate structured JSON from a prompt and response.

---

## ⚙️ Setup

For these examples, assume you have:

```python
from result import Result, Ok, Err
from task import SyncTask, AsyncTask, AbstractSyncTask, AbstractAsyncTask

TEXT = """
The Future of AI: How Generative Models Are Changing Creativity.
Artificial intelligence is rapidly evolving. In this post, we explore its implications in art, music, and writing.
"""

```

## 🛠️ Synchronous Task Example as Function

```python
import json

@SyncTask
def simulate_structure_sync(text: str) -> Result[dict, str]:
    try:
        return Ok({
            "title": "The Future of AI",
            "summary": "Explores AI's role in creativity.",
            "tags": ["AI", "Generative", "Creativity"]
        })
    except Exception as e:
        return Err(f"Failed to simulate structure: {e}")

result = simulate_structure_sync(TEXT)
if result.is_ok():
    structured_data = result.unwrap()
    print(json.dumps(structured_data, indent=2))
else:
    print(f"Error: {result.unwrap_err()}")
```

## 🛠️ Synchronous Task Example as Class

```python
from task import AbstractSyncTask

class SimulatedSyncTask(AbstractSyncTask[dict, str]):
    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self) -> Result[dict, str]:
        return Ok({
            "title": "The Future of AI",
            "summary": "Explores AI's role in creativity.",
            "tags": ["AI", "Generative", "Creativity"]
        })

task = SimulatedSyncTask(TEXT)
result = task()
if result.is_ok():
    structured_data = result.unwrap()
    print(json.dumps(structured_data, indent=2))
else:
    print(f"Error: {result.unwrap_err()}")
```

## 🛠️ Asynchronous Task Example as Function

```python
import openai
from task import AsyncTask

@AsyncTask
async def extract_structure(text: str) -> Result[dict, str]:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract title, summary, and tags from input text. Return JSON."},
                {"role": "user", "content": text},
            ]
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return Ok(data)
    except Exception as e:
        return Err(f"Failed to extract structure: {e}")

async def main():
    result = await extract_structure(TEXT)
    if result.is_ok():
        structured_data = result.unwrap()
        print(json.dumps(structured_data, indent=2))
    else:
        print(f"Error: {result.unwrap_err()}")

import asyncio
asyncio.run(main())
```

## 🛠️ Asynchronous Task Example as Class

```python
from task import AbstractAsyncTask

class ExtractAsyncTask(AbstractAsyncTask[dict, str]):
    def __init__(self, text: str):
        super().__init__(retries=2)
        self.text = text

    async def run(self) -> Result[dict, str]:
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Extract title, summary, and tags. Return JSON."},
                    {"role": "user", "content": self.text},
                ]
            )
            return Ok(json.loads(response.choices[0].message.content))
        except Exception as e:
            return Err(str(e))

async def main():
    task = ExtractAsyncTask(TEXT)
    result = await task()
    if result.is_ok():
        structured_data = result.unwrap()
        print(json.dumps(structured_data, indent=2))
    else:
        print(f"Error: {result.unwrap_err()}")

import asyncio
asyncio.run(main())
```


The `Task` module provides a powerful way to handle both synchronous and asynchronous tasks with built-in error handling and retry logic. You can choose between function-based or class-based implementations based on your needs. The examples above demonstrate how to extract structured data from text using both approaches.
This allows for flexibility in how you design your tasks, making it easier to integrate with existing codebases or frameworks.
The `Task` module is particularly useful for wrapping SDK calls, such as OpenAI's API, where you may want to handle retries and errors gracefully.
