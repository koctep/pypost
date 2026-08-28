"""Collection variable model and validation logic (PYPOST-1220).

Defines the variable schema used in self-contained collections, including
type whitelisting, default value type validation, and preset profile support.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

COLLECTION_VARIABLE_TYPES: frozenset[str] = frozenset(
    {"string", "integer", "number", "boolean", "array", "object"}
)


def validate_variable_value(value: Any, var_type: str) -> bool:
    """Validate a variable value against its declared type name.

    Args:
        value: The value to validate.
        var_type: The expected type name ('string', 'integer', 'number',
            'boolean', 'array', 'object').

    Returns:
        True if the value matches the type, False otherwise.
    """
    if var_type == "string":
        return isinstance(value, str)
    if var_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if var_type == "number":
        return (isinstance(value, (int, float))) and not isinstance(value, bool)
    if var_type == "boolean":
        return isinstance(value, bool)
    if var_type == "array":
        return isinstance(value, list)
    if var_type == "object":
        return isinstance(value, dict)
    return False


class CollectionVariable(BaseModel):
    """Metadata schema for one variable defined in a self-contained collection."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    type: str = "string"
    default: Optional[Any] = Field(default=None, alias="default_value")
    description: str = ""
    required: bool = False
    secret: bool = False

    @property
    def default_value(self) -> Optional[Any]:
        """Alias property for default."""
        return self.default

    def model_post_init(self, __context: Any) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Variable name cannot be empty")
        if self.type not in COLLECTION_VARIABLE_TYPES:
            raise ValueError(f"Unsupported variable type: {self.type}")
        self._validate_default_type()

    def _validate_default_type(self) -> None:
        """Validate that default is compatible with type when not None."""
        if self.default is None:
            return
        if not validate_variable_value(self.default, self.type):
            raise ValueError(
                f"Default value {self.default!r} is not valid for variable type {self.type!r}"
            )
