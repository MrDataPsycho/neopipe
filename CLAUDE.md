# NeoPipe - Python Function Orchestration Library

## Overview
NeoPipe is a Python library for seamless function orchestration, inspired by Rust and scikit-learn pipelines. It provides a clean API for workflow management in microservices and AI-powered applications with monadic error handling using Rust-style Result types.

## AI Agent Context & Guidance

### **Library Purpose**
- **Primary Use**: Python library for function orchestration inspired by Rust and scikit-learn pipelines
- **Target Applications**: Microservices and AI-powered applications
- **Core Philosophy**: Rust-style Result type with monadic error handling - no exceptions in normal flow

### **Key Architecture Principles**
1. **No exception throwing** in task execution - everything returns `Result[T, E]`
2. **Composable pipelines** - tasks can be chained and reused  
3. **Retry logic** built into base task classes
4. **Debug tracing** for pipeline execution analysis
5. **Both sync and async** support throughout

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
├── tests/                 # Test suite with comprehensive coverage
├── docs/                  # MkDocs documentation
├── notebooks/             # Jupyter notebooks with examples
│   └── examples/          # Real-world usage examples (OpenAI integration)
├── pyproject.toml         # Project configuration and dependencies
├── mkdocs.yml            # Documentation configuration
└── README.md             # Project overview
```

## Core Components

### 1. Result Type System (`src/neopipe/result.py`)
- **Result[T, E]**: Core monadic error handling type
  - `Ok` and `Err` variants  
  - Supports `map`, `and_then`, `unwrap` operations
  - **Missing Methods**: `unwrap_err`, `expect_err`, `err_or`, `err_or_else` (common in Rust)
- **ExecutionResult[T, E]**: Unified result container for pipeline runs
  - Wraps results with timing and optional trace information
  - Handles both single results and lists of results
- **Trace[T, E]**: Sequential trace of one pipeline execution
- **Traces[T, E]**: Collection of multiple pipeline traces

### 2. Tasks (`src/neopipe/task.py`)
**Synchronous Tasks:**
- `BaseSyncTask[T, E]` / `BaseAsyncTask[T, E]` - Abstract base classes
- `FunctionSyncTask` / `FunctionAsyncTask` - Function wrappers with decorators
- `ClassSyncTask` / `ClassAsyncTask` - Class-based tasks

**Key Features:**
- All tasks operate on `Result[T, E]` → `Result[U, E]`
- Automatic retry logic with exponential backoff
- Comprehensive logging with task IDs
- Type-safe Result input/output
- Decorator support for functions

### 3. Pipelines
**SyncPipeline** (`src/neopipe/pipeline.py`) - Sequential synchronous execution
**AsyncPipeline** (`src/neopipe/async_pipeline.py`) - Async execution with modes:
- `run()`: Concurrent task execution (1:1 with inputs)
- `run_sequence()`: Sequential task chaining  
- `run_parallel()`: Concurrent pipeline execution
- Support debug mode with `Trace` / `Traces`

### 4. Usage Patterns
- **Task Definition**: Use decorators or class inheritance
- **Pipeline Creation**: Chain tasks with `from_tasks()` or `add_task()`
- **Execution**: `run()`, `run_sequence()`, `run_parallel()` methods
- **Error Handling**: All operations return `Result[T, E]` - no exceptions in normal flow

## Testing Structure
- Comprehensive test coverage in `tests/`
- Test files: `test_async_pipeline.py`, `test_sync_pipeline.py`, `test_task.py`, `test_result.py`, etc.
- Examples in `docs/examples/` and `notebooks/`
- Real-world examples like OpenAI integration

## Dependencies & Build System

### Runtime Dependencies
- **Zero dependencies** (pure Python)

### Development Dependencies  
- **Testing**: pytest, pytest-cov, pytest-mock, pytest-asyncio
- **Development**: ruff (linting), mypy (type checking), isort (import sorting)
- **Documentation**: mkdocs, mkdocs-material, mkdocstrings
- **Examples**: httpx, pydantic, openai, python-dotenv

### Build Configuration
- **Backend**: Hatchling (modern Python packaging)
- **Python Support**: 3.10, 3.11, 3.12
- **Package Manager**: Uses Hatch environment management

### Common Development Commands
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

## Target Use Cases
The library is specifically designed for:
- **AI Applications**: Orchestrating API calls (OpenAI, Claude, other 3rd party APIs)
- **Microservices**: Workflow management and service orchestration
- **Data Pipelines**: Complex data processing with tracing needs
- **Error-prone Operations**: Robust error handling without exceptions

## Code Quality Standards
- **Modern Python**: Type hints throughout, Python 3.10+ features
- **Structured Data**: Dataclasses and generics for type safety
- **Logging**: Comprehensive logging with task IDs
- **Zero Runtime Dependencies**: Pure Python implementation
- **Testing**: High test coverage with pytest
- **Documentation**: MkDocs with examples and API reference

## Current Development Status
- **Version**: 0.1.1 (active development)
- **Branch**: feat/replicate-task
- **Recent Focus**: Enhanced tracing, execution results, error propagation
- **Known Issues**: Missing `unwrap_err`, `expect_err` methods in Result type

## Important Notes for AI Agents
1. **Always preserve the Result[T, E] pattern** - don't introduce exceptions in task execution
2. **Maintain type safety** - use proper generics and type hints
3. **Follow existing patterns** - sync/async task classes, pipeline execution modes
4. **Add comprehensive tests** - all new features need test coverage
5. **Update documentation** - keep examples and API docs current
6. **Consider backward compatibility** - this is a public library
7. **Use library-level imports ONLY** - Never use relative imports (`.module`), always use `neopipe.module`

## Import Guidelines
- ✅ **Correct**: `from neopipe.result import Result, Ok, Err`
- ✅ **Correct**: `from neopipe.task import BaseSyncTask`
- ✅ **Correct**: `from neopipe.pipeline import SyncPipeline`
- ❌ **Incorrect**: `from .result import Result, Ok, Err`
- ❌ **Incorrect**: `from .task import BaseSyncTask`
- ❌ **Incorrect**: `from .pipeline import SyncPipeline`

**Rationale**: Library-level imports ensure consistent module resolution, avoid circular import issues, and make the code more maintainable and predictable across different execution contexts.