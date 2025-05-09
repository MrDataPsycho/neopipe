from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Awaitable, Callable, Generic, List, Self, Tuple, TypeVar, Union, Optional

T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Transformed success/error type


class UnwrapError(Exception):
    """Raised when unwrap is called on an Err value."""
    pass


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """A Rust-style Result type for monadic error handling in Python."""

    _is_ok: bool
    _value: Union[T, E]

    @staticmethod
    def Ok(value: T) -> Self:
        """
        Create a Result representing a successful value.

        Args:
            value: The success value.

        Returns:
            Result[T, E]: An Ok variant.
        """
        return Result(True, value)

    @staticmethod
    def Err(error: E) -> Self:
        """
        Create a Result representing an error.

        Args:
            error: The error value.

        Returns:
            Result[T, E]: An Err variant.
        """
        return Result(False, error)

    def is_ok(self) -> bool:
        """
        Check if the result is Ok.

        Returns:
            bool: True if Ok, False otherwise.
        """
        return self._is_ok

    def is_err(self) -> bool:
        """
        Check if the result is Err.

        Returns:
            bool: True if Err, False otherwise.
        """
        return not self._is_ok

    def ok(self) -> Union[T, None]:
        """
        Get the success value if available.

        Returns:
            T | None: The Ok value or None.
        """
        return self._value if self._is_ok else None

    def err(self) -> Union[E, None]:
        """
        Get the error value if available.

        Returns:
            E | None: The Err value or None.
        """
        return self._value if not self._is_ok else None

    def map(self, op: Callable[[T], U]) -> Result[U, E]:
        """
        Apply a function to the Ok value.

        Args:
            op: A function that transforms the success value.

        Returns:
            Result[U, E]: A new Result with transformed success or the original error.
        """
        if self._is_ok:
            return Result.Ok(op(self._value))  # type: ignore
        return Result.Err(self._value)  # type: ignore

    async def map_async(self, op: Callable[[T], Awaitable[U]]) -> Result[U, E]:
        """
        Asynchronously apply a function to the Ok value.

        Args:
            op: An async function that transforms the success value.

        Returns:
            Result[U, E]: A new Result with transformed success or the original error.
        """
        if self._is_ok:
            return Result.Ok(await op(self._value))  # type: ignore
        return Result.Err(self._value)  # type: ignore

    def map_err(self, op: Callable[[E], U]) -> Result[T, U]:
        """
        Apply a function to the Err value.

        Args:
            op: A function that transforms the error value.

        Returns:
            Result[T, U]: A new Result with transformed error or the original success.
        """
        if self._is_ok:
            return Result.Ok(self._value)  # type: ignore
        return Result.Err(op(self._value))  # type: ignore

    async def map_err_async(self, op: Callable[[E], Awaitable[U]]) -> Result[T, U]:
        """
        Asynchronously apply a function to the Err value.

        Args:
            op: An async function that transforms the error value.

        Returns:
            Result[T, U]: A new Result with transformed error or the original success.
        """
        if self._is_ok:
            return Result.Ok(self._value)  # type: ignore
        return Result.Err(await op(self._value))  # type: ignore

    def and_then(self, op: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """
        Chain another Result-returning function if current is Ok.

        Args:
            op: A function that takes a success value and returns a new Result.

        Returns:
            Result[U, E]: The new chained result, or the original error.
        """
        if self._is_ok:
            return op(self._value)  # type: ignore
        return Result.Err(self._value)  # type: ignore

    async def and_then_async(
        self, op: Callable[[T], Awaitable[Result[U, E]]]
    ) -> Result[U, E]:
        """
        Asynchronously chain another Result-returning function if current is Ok.

        Args:
            op: An async function that takes a success value and returns a new Result.

        Returns:
            Result[U, E]: The new chained result, or the original error.
        """
        if self._is_ok:
            return await op(self._value)  # type: ignore
        return Result.Err(self._value)  # type: ignore

    def unwrap(self) -> T:
        """
        Extract the success value or raise an error.

        Returns:
            T: The Ok value.

        Raises:
            UnwrapError: If the result is Err.
        """
        if self._is_ok:
            return self._value  # type: ignore
        raise UnwrapError(f"Called unwrap on Err: {self._value}")

    def unwrap_or(self, default: T) -> T:
        """
        Return the success value or a default.

        Args:
            default: The fallback value.

        Returns:
            T: The Ok value or the default.
        """
        return self._value if self._is_ok else default  # type: ignore

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        """
        Return the success value or a value generated from the error.

        Args:
            op: A function that maps the error to a fallback value.

        Returns:
            T: The Ok value or a fallback derived from the error.
        """
        return self._value if self._is_ok else op(self._value)  # type: ignore

    def expect(self, msg: str) -> T:
        """
        Extract the success value or raise with a custom message.

        Args:
            msg: The message to include in the exception.

        Returns:
            T: The Ok value.

        Raises:
            UnwrapError: If the result is Err.
        """
        if self._is_ok:
            return self._value  # type: ignore
        raise UnwrapError(f"{msg}: {self._value}")

    def match(self, ok_fn: Callable[[T], U], err_fn: Callable[[E], U]) -> U:
        """
        Pattern match to handle both Ok and Err branches.

        Args:
            ok_fn: Function to handle Ok.
            err_fn: Function to handle Err.

        Returns:
            U: Result of executing the appropriate handler.
        """
        if self._is_ok:
            return ok_fn(self._value)  # type: ignore
        return err_fn(self._value)  # type: ignore

    def to_dict(self) -> dict:
        """Converts the Result to a dictionary.

        Returns:
            dict: The Result as a dictionary
        """
        return asdict(self)

    def to_json(self) -> str:
        """Converts the Result to a JSON string.

        Returns:
            str: The Result as a JSON string
        """
        return json.dumps(self.to_dict())

    def __repr__(self) -> str:
        """
        Return a string representation of the Result.

        Returns:
            str: Ok(value) or Err(error).
        """
        variant = "Ok" if self._is_ok else "Err"
        return f"{variant}({self._value!r})"


def Ok(value: T) -> Result[T, None]:
    """Creates an Ok Result with the given value."""
    return Result(True, value)


def Err(error: E) -> Result[None, E]:
    """Creates an Err Result with the given error."""
    return Result(False, error)


@dataclass
class Trace(Generic[T, E]):
    """
    A sequential trace of one pipeline:
    steps is a list of (task_name, Result[T, E]).
    """
    steps: List[Tuple[str, Result[T, E]]]

    def __getitem__(self, index: int) -> Tuple[str, Result[T, E]]:
        """Get a step by index."""
        return self.steps[index]
    
    def __iter__(self):
        """Iterate over the steps."""
        return iter(self.steps)

    def __len__(self) -> int:
        return len(self.steps)

    def __repr__(self):
        return f"Trace(steps={self.steps!r})"


@dataclass
class Traces(Generic[T, E]):
    """
    A collection of per-pipeline traces.
    pipelines is a list of Trace[T, E].
    """
    pipelines: List[Trace[T, E]]

    def __getitem__(self, index: int) -> Trace[T, E]:
        """Get a trace by index."""
        return self.pipelines[index]
    
    def __iter__(self):
        """Iterate over the traces."""
        return iter(self.pipelines)

    def __len__(self) -> int:
        return len(self.pipelines)

    def __repr__(self):
        return f"Traces(pipelines={self.pipelines!r})"


@dataclass
class ExecutionResult(Generic[T, E]):
    """
    The unified result container for piping runs.

    Attributes:
      result: Either a Result[T, E] (single pipeline) or
              List[Result[T, E]] (parallel pipelines).
      trace:  Optional Trace[T, E] or Traces[T, E] if debug=True.
      execution_time: Elapsed time in seconds.
      time_unit: Always 's'.
    """
    result: Union[Result[T, E], List[Result[T, E]]]
    trace: Optional[Union[Trace[T, E], Traces[T, E]]]
    execution_time: float
    time_unit: str = "s"

    def value(self) -> Union[T, List[T]]:
        """
        Extract the inner success value(s). If any entry is Err, raises.
        """
        if isinstance(self.result, list):
            return [r.unwrap() for r in self.result]
        return self.result.unwrap()
    
    def unwrap(self) -> Union[Result[T, E], List[Result[T, E]]]:
        if self.is_ok():
            return self.result
        raise UnwrapError(f"Called unwrap on Err: {self.result}")
    
    def is_ok(self) -> bool:
        if isinstance(self.result, list):
            return all(r.is_ok() for r in self.result)
        return self.result.is_ok()

    def is_err(self) -> bool:
        if isinstance(self.result, list):
            return any(r.is_err() for r in self.result)
        return self.result.is_err()


    def __len__(self) -> int:
        
        if isinstance(self.result, list):
            return len(self.result)
        return 1

    def __repr__(self) -> str:
        base = (
            f"ExecutionResult(result={self.result!r}, "
            f"execution_time={self.execution_time:.3f}{self.time_unit}"
        )
        if self.trace is not None:
            base += f", trace={self.trace!r}"
        base += ")"
        return base

    def __str__(self) -> str:
        return self.__repr__()

