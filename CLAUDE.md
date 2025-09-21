# NeoPipe - Python Function Orchestration Library

## Overview
NeoPipe is a Python library for seamless function orchestration, inspired by Rust and scikit-learn pipelines. It provides a clean API for workflow management in microservices and AI-powered applications with monadic error handling using Rust-style Result types.

## Project Structure
```
neopipe/
├── src/neopipe/           # Main source code
│   ├── __init__.py        # Package initialization with logging setup
│   ├── __about__.py       # Version info (v0.1.1)
│   ├── result.py          # Result/Ok/Err types and ExecutionResult
│   ├── task.py            # Sync/Async task base classes
│   ├── pipeline.py        # Synchronous pipeline implementation
│   └── async_pipeline.py  # Asynchronous pipeline implementation
├── tests/                 # Test suite
├── docs/                  # MkDocs documentation
├── pyproject.toml         # Project configuration and dependencies
├── mkdocs.yml            # Documentation configuration
└── README.md             # Project overview
```

## Core Concepts

### 1. Result Type System
- **Result[T, E]**: Monadic error handling container (generic over success type T and error type E)
- **Ok(value)**: Success variant containing a value
- **Err(error)**: Error variant containing an error
- **ExecutionResult**: Container for pipeline execution results with timing and optional traces

### 2. Task System
**Synchronous Tasks:**
- `BaseSyncTask[T, E]`: Abstract base class for sync tasks
- `FunctionSyncTask`: Wraps functions that take/return Result[T, E]
- `ClassSyncTask`: For stateful/configurable sync tasks

**Asynchronous Tasks:**
- `BaseAsyncTask[T, E]`: Abstract base class for async tasks
- `FunctionAsyncTask`: Wraps async functions
- `ClassAsyncTask`: For stateful async tasks

**Task Features:**
- Automatic retry logic with exponential backoff
- Comprehensive logging with task IDs
- Type-safe Result[T, E] input/output
- Decorator support for functions

### 3. Pipeline System
**SyncPipeline[T, E]:**
- Sequential execution of BaseSyncTasks
- Passes Result[T, E] through each step
- Support for parallel execution of multiple pipelines
- Debug mode with execution traces

**AsyncPipeline[T, E]:**
- Three execution modes:
  - `run()`: Concurrent task execution (1:1 with inputs)
  - `run_sequence()`: Sequential task chaining
  - `run_parallel()`: Concurrent pipeline execution
- Debug tracing support

### 4. Tracing and Results
- **Trace[T, E]**: Sequential trace of one pipeline execution
- **Traces[T, E]**: Collection of multiple pipeline traces
- **ExecutionResult[T, E]**: Unified result container with timing and optional traces

## Build System & Tools

### Dependencies
- **Runtime**: Zero dependencies (pure Python)
- **Testing**: pytest, pytest-cov, pytest-mock, pytest-asyncio
- **Development**: ruff (linting), mypy (type checking), isort (import sorting)
- **Documentation**: mkdocs, mkdocs-material, mkdocstrings
- **Examples**: httpx, pydantic, openai, dotenv

### Build System
- **Backend**: Hatchling (modern Python packaging)
- **Python Support**: 3.10, 3.11, 3.12
- **Package Manager**: Uses Hatch environment management

### Development Commands
```bash
# Install in editable mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev,testing]"

# Run tests with coverage
pytest --cov=src/neopipe --cov-report=term-missing

# Type checking
mypy --install-types --non-interactive src/neopipe tests

# Linting and formatting
ruff check src/ tests/
ruff format src/ tests/

# Documentation
mkdocs serve --dev-addr localhost:8000
mkdocs build --clean --strict
```

## Key Design Patterns

### 1. Monadic Error Handling
All operations use Result[T, E] for composable error handling:
```python
from neopipe import Result, Ok, Err

def safe_divide(result: Result[tuple[int, int], str]) -> Result[float, str]:
    if result.is_err():
        return result
    a, b = result.unwrap()
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)
```

### 2. Task Composition
Tasks can be created as functions or classes:
```python
# Function-based task
@FunctionSyncTask.decorator(retries=2)
def process_data(result: Result[Data, str]) -> Result[ProcessedData, str]:
    # Implementation
    pass

# Class-based task
class CustomTask(ClassSyncTask[Input, str]):
    def execute(self, input_result: Result[Input, str]) -> Result[Output, str]:
        # Implementation
        pass
```

### 3. Pipeline Execution
```python
# Sync pipeline
pipeline = SyncPipeline.from_tasks([task1, task2, task3])
exec_result = pipeline.run(Ok(initial_data), debug=True)

# Async pipeline
pipeline = AsyncPipeline.from_tasks([async_task1, async_task2])
exec_result = await pipeline.run_sequence(Ok(initial_data), debug=True)
```

## Testing Strategy
- Comprehensive test suite in `tests/` directory
- Tests for all core components: result, task, sync_pipeline, async_pipeline
- Coverage reporting configured in pyproject.toml
- Async testing support with pytest-asyncio

## Documentation
- **Format**: MkDocs with Material theme
- **Structure**: API reference + examples
- **Location**: `docs/` directory
- **Build**: `mkdocs build/serve`

## AI/Microservices Focus
The library is specifically designed for:
- Orchestrating API calls (OpenAI, Claude, other 3rd party APIs)
- Microservices workflow management
- Error-prone operations requiring robust error handling
- Complex data pipelines with tracing needs

## Code Style & Quality
- Modern Python with type hints
- Dataclasses for structured data
- Comprehensive logging
- Zero external runtime dependencies
- Type checking with mypy
- Linting with ruff
- Import organization with isort


## Recent Development
- Added better tracing with Complete Execution result
- Improved pipeline execution result handling
- Enhanced error propagation and debugging capabilities