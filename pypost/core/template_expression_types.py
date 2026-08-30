from __future__ import annotations

from dataclasses import dataclass


class IntegerConversionError(Exception):
    """Raised when a ``to_int`` template expression cannot be processed safely."""


@dataclass(frozen=True, init=False)
class ExpressionFailureProvenance:
    """Structured provenance describing an expression failure and strict conversion status."""

    code: str
    expression: str
    function_name: str | None = None
    is_strict_conversion: bool = False
    span: tuple[int, int] | None = None

    def __init__(
        self,
        code: str,
        expression: str = "",
        function_name: str | None = None,
        is_strict_conversion: bool = False,
        span: tuple[int, int] | None = None,
        is_strict: bool | None = None,
    ) -> None:
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "expression", expression)
        object.__setattr__(self, "function_name", function_name)
        strict_val = is_strict if is_strict is not None else is_strict_conversion
        object.__setattr__(self, "is_strict_conversion", strict_val)
        object.__setattr__(self, "span", span)

    @property
    def is_strict(self) -> bool:
        """Backward-compatibility alias for ``is_strict_conversion``."""
        return self.is_strict_conversion


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    code: str | None = None
    function_name: str | None = None
    expression: str | None = None
    failures: tuple[ExpressionFailureProvenance, ...] = ()

    @property
    def has_strict_failure(self) -> bool:
        """True if any recorded failure involves a strict conversion function."""
        return any(f.is_strict_conversion for f in self.failures)

    @classmethod
    def valid(cls) -> "ValidationResult":
        return cls(is_valid=True)

    @classmethod
    def error(
        cls,
        code: str,
        function_name: str | None = None,
        expression: str | None = None,
        failures: tuple[ExpressionFailureProvenance, ...] = (),
    ) -> "ValidationResult":
        return cls(
            is_valid=False,
            code=code,
            function_name=function_name,
            expression=expression,
            failures=failures,
        )
