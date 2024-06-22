from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, Optional
import json

T = TypeVar('T')
E = TypeVar('E')

@dataclass
class Result(Generic[T, E]):
    value: Optional[T] = field(default=None)
    error: Optional[E] = field(default=None)

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

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

# Utility functions
def Ok(value: T) -> Result[T, None]:
    return Result(value=value)

def Err(error: E) -> Result[None, E]:
    return Result(error=error)


def Ok(value: T) -> Result[T, None]:
    return Result(value=value)

def Err(error: E) -> Result[None, E]:
    return Result(error=error)
