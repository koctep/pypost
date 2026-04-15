import re

from pypost.core.function_registry import FunctionRegistry
from pypost.core.template_expression_types import ValidationResult


class FunctionExpressionResolver:
    _IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    _FUNCTION_SIGNATURE_RE = re.compile(
        r"^(?P<func>[a-zA-Z_][a-zA-Z0-9_]*)\((?P<args>.*)\)$"
    )

    def __init__(self, registry: FunctionRegistry) -> None:
        self._registry = registry

    def validate_content(self, content: str) -> ValidationResult:
        """Scan {{...}} tokens and validate each inner expression."""
        expressions = re.findall(r"\{\{\s*(.*?)\s*\}\}", content)
        for expression in expressions:
            validation_error = self._validate_expression(expression.strip())
            if validation_error:
                return validation_error

        return ValidationResult.valid()

    def _validate_expression(self, expression: str) -> ValidationResult | None:
        if self._IDENTIFIER_RE.fullmatch(expression):
            return None

        parsed_expression = self._parse_function_expression(expression)
        if isinstance(parsed_expression, ValidationResult):
            return parsed_expression

        function_name, args = parsed_expression
        return self._validate_function_args(function_name, args)

    def _parse_function_expression(
        self, expression: str,
    ) -> tuple[str, str] | ValidationResult:
        function_match = self._FUNCTION_SIGNATURE_RE.fullmatch(expression)
        if not function_match:
            return ValidationResult.error("invalid_syntax")

        function_name = function_match.group("func")
        if not self._registry.is_allowed(function_name):
            return ValidationResult.error("unknown_function", function_name)

        return function_name, function_match.group("args").strip()

    def _validate_function_args(
        self, function_name: str, args: str,
    ) -> ValidationResult | None:
        argument = self._extract_single_argument(args)
        if argument is None:
            return ValidationResult.error("invalid_arity", function_name)

        if self._IDENTIFIER_RE.fullmatch(argument):
            return None

        if not self._FUNCTION_SIGNATURE_RE.fullmatch(argument):
            return ValidationResult.error("invalid_argument", function_name)

        validation_error = self._validate_expression(argument)
        if validation_error:
            if validation_error.code == "invalid_arity":
                return ValidationResult.error("invalid_argument", function_name)
            return validation_error
        return None

    def _extract_single_argument(self, args: str) -> str | None:
        """
        Returns single argument preserving nested call expression support.
        Returns None when there are multiple top-level arguments.
        """
        depth = 0
        for char in args:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(0, depth - 1)
            elif char == "," and depth == 0:
                return None
        return args.strip()
