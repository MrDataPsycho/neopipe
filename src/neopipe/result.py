from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, Optional
import json

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Result(Generic[T, E]):
    """Result type for the neopipe package."""
    value: Optional[T] = field(default=None)
    error: Optional[E] = field(default=None)

    def is_ok(self) -> bool:
        """Checks if the Result is an Ok value.

        Returns:
            bool: True if the Result is an Ok value, False otherwise
        """
        return self.error is None

    def is_err(self) -> bool:
        """Checks if the Result is an Err value."""
        return self.error is not None

    def unwrap(self) -> T:
        """Unwraps the Result value if it is an Ok value, otherwise raises a ValueError.

        Raises:
            ValueError: If the Result is an Err value

        Returns:
            T: The unwrapped value
        """
        if self.is_err():
            raise ValueError(f"Called unwrap on an Err value: {self.error}")
        return self.value

    def unwrap_err(self) -> E:
        """Unwraps the Result error if it is an Err value, otherwise raises a ValueError.

        Raises:
            ValueError: If the Result is an Ok value

        Returns:
            E: The unwrapped error
        """
        if self.is_ok():
            raise ValueError(f"Called unwrap_err on an Ok value: {self.value}")
        return self.error

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


def Ok(value: T) -> Result[T, None]:
    """Creates an Ok Result with the given value."""
    return Result(value=value)


def Err(error: E) -> Result[None, E]:
    """Creates an Err Result with the given error."""
    return Result(error=error)

