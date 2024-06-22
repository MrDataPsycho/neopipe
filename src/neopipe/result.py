from typing import TypeVar, Generic, Optional


T = TypeVar('T')
E = TypeVar('E')

class Result(Generic[T, E]):
    def __init__(self, value: Optional[T] = None, error: Optional[E] = None):
        self.value = value
        self.error = error

    def is_ok(self) -> bool:
        return self.error is None

    def is_err(self) -> bool:
        return self.error is not None

    def unwrap(self) -> T:
        if self.is_err():
            raise ValueError(f"Called unwrap on an Err value: {self.error}")
        return self.value

    def unwrap_err(self) -> E:
        if self.is_ok():
            raise ValueError(f"Called unwrap_err on an Ok value: {self.value}")
        return self.error

def Ok(value: T) -> Result[T, None]:
    return Result(value=value)

def Err(error: E) -> Result[None, E]:
    return Result(error=error)
