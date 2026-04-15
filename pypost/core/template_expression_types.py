from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    code: str | None = None
    function_name: str | None = None

    @classmethod
    def valid(cls) -> "ValidationResult":
        return cls(is_valid=True)

    @classmethod
    def error(cls, code: str, function_name: str | None = None) -> "ValidationResult":
        return cls(is_valid=False, code=code, function_name=function_name)
