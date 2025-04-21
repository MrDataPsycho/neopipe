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
print(Ok("hello").unwrap())  # "hello"
print(Err("boom").unwrap_or("default"))  # "default"
print(Err("fail").unwrap_or_else(lambda e: f"Handled: {e}"))  # "Handled: fail"
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
```
