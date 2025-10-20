# 🧩 Using the `Result` Class

The `Result` class is a core utility in this library for representing **success** (`Ok`) or **failure** (`Err`) outcomes, inspired by Rust.

It eliminates the need for try/except blocks by returning an object that contains either a valid value or an error.

---

## ✅ Why use `Result`?

- Clear separation of success and error flows
- Functional style: `map`, `and_then`, `unwrap`, etc.
- Built-in support for retries and task composition
- Consistent return type for sync and async code

---

## 📦 Importing `Result`

```python
from result import Result, Ok, Err
```

## Creating a Result

```python
success = Ok(42)
failure = Err("Something went wrong")

print(success)  # Ok(42)
print(failure)  # Err('Something went wrong')

# Checking and Accessing Values
if success.is_ok():
    print("Value:", success.unwrap())

if failure.is_err():
    print("Error:", failure.err())

```

## 🔁 Transforming with `map` and `map_err`
```
result = Ok(5).map(lambda x: x * 2)  # Ok(10)

error_result = Err("bad input").map_err(lambda e: f"Error: {e}")
# Err("Error: bad input")
```

## 🔗 Chaining with `and_then`

```python
def safe_divide(x: int, y: int) -> Result[float, str]:
    if y == 0:
        return Err("Division by zero")
    return Ok(x / y)

result = Ok((10, 2)).and_then(lambda pair: safe_divide(*pair))
# Ok(5.0)
```

## 🧯 Unwrapping and Defaults

```python
# Success path unwrapping
print(Ok("hello").unwrap())  # "hello"
print(Ok("hello").expect("Should be a value"))  # "hello"

# Error path unwrapping (NEW in v0.1.2!)
print(Err("boom").unwrap_err())  # "boom"
print(Err("boom").expect_err("Should be an error"))  # "boom"

# Defaults and fallbacks
print(Err("boom").unwrap_or("default"))  # "default"
print(Err("fail").unwrap_or_else(lambda e: f"Handled: {e}"))  # "Handled: fail"

# Error defaults (NEW in v0.1.2!)
print(Ok("success").err_or("no error"))  # "no error"
print(Err("actual error").err_or("no error"))  # "actual error"
print(Ok("success").err_or_else(lambda x: f"Error from {x}"))  # "Error from success"
```

## ⚡ Pattern Matching

```python
result = Ok(100)

message = result.match(
    ok_fn=lambda x: f"Success: {x}",
    err_fn=lambda e: f"Failure: {e}"
)

print(message)  # Success: 100
```

## 🌐 Async Support
The Result object includes async versions of map, map_err, and and_then.

```python
async def double_async(x: int) -> int:
    return x * 2

result = await Ok(5).map_async(double_async)
# Ok(10)

async def validate(x: int) -> Result[str, str]:
    return Ok(f"value: {x}") if x > 0 else Err("Too small")

result = await Ok(3).and_then_async(validate)
# Ok("value: 3")
```

## 🧪 Real World Usage

```python
def get_user(user_id: int) -> Result[dict, str]:
    if user_id == 42:
        return Ok({"id": 42, "name": "Douglas"})
    return Err("User not found")

# Using the new error handling methods
def process_user_request(user_id: int):
    result = get_user(user_id)
    
    if result.is_ok():
        user = result.unwrap()
        print(f"Found user: {user['name']}")
    else:
        # Use new unwrap_err method
        error = result.unwrap_err()
        print(f"Request failed: {error}")
        
        # Or use expect_err with custom message
        detailed_error = result.expect_err("Expected user lookup to fail")
        print(f"Detailed: {detailed_error}")

# Example with error defaults
def get_error_message(result: Result[str, str]) -> str:
    # Get error or provide default
    return result.err_or("No error occurred")
    
# Usage
success_result = Ok("Operation completed")
error_result = Err("Network timeout")

print(get_error_message(success_result))  # "No error occurred"
print(get_error_message(error_result))    # "Network timeout"
```

## 🆕 New in v0.1.2

The Result class now includes additional Rust-inspired methods:

- `unwrap_err()` - Extract error value or raise
- `expect_err(msg)` - Extract error value with custom message
- `err_or(default)` - Get error value or default
- `err_or_else(op)` - Get error value or compute from success value

These methods complete the Result API and provide better symmetry with Rust's Result type.
