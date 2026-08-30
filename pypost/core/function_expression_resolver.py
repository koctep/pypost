from __future__ import annotations

import logging
import re

from typing import Any

from pypost.core.function_registry import FunctionRegistry
from pypost.core.template_expression_tokenizer import (
    TEMPLATE_PLACEHOLDER_PATTERN,
    tokenize_template_expressions,
)
from pypost.core.template_expression_types import (
    ExpressionFailureProvenance,
    IntegerConversionError,
    ValidationResult,
)

NESTED_FUNCTION_CALLS_ALLOWED: bool = True

logger = logging.getLogger(__name__)


class FunctionExpressionResolver:
    """Validates ``{{...}}`` expressions.

    Nested policy: when ``NESTED_FUNCTION_CALLS_ALLOWED`` is True, a function argument may be
    a safe variable path or another allow-listed single-argument function call, validated
    recursively via ``FunctionRegistry``. There is no fixed depth limit as long as each call
    satisfies catalog membership and single-argument rules.
    """

    # Safe path: first segment may start with `_`; later segments must not
    # (blocks ``db.__class__`` / ``mcp.request.__class__``).
    _SAFE_PATH_RE = re.compile(
        r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)*$"
    )
    _FUNCTION_SIGNATURE_RE = re.compile(r"^(?P<func>[a-zA-Z_][a-zA-Z0-9_]*)\((?P<args>.*)\)$")
    _FUNCTION_CALL_NAME_RE = re.compile(r"(?<!\.)\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
    _IDENTIFIER_RE = re.compile(r"(?<!\.)\b([a-zA-Z_][a-zA-Z0-9_]*)\b")

    def __init__(self, registry: FunctionRegistry) -> None:
        self._registry = registry

    def extract_function_names(self, expression: str) -> list[str]:
        """Extract all function names called in expression (outer and nested)."""
        return self._FUNCTION_CALL_NAME_RE.findall(expression)

    def contains_strict_function(self, expression: str) -> bool:
        """Return True if any function in the expression is a strict conversion function."""
        return any(
            self._registry.is_strict_conversion(fn)
            for fn in self.extract_function_names(expression)
        )

    def validate_content(self, content: str) -> ValidationResult:
        """Scan {{...}} tokens and validate each inner expression."""
        return self.validate_expressions(tokenize_template_expressions(content))

    def validate_expressions(self, expressions: list[str]) -> ValidationResult:
        """Validate pre-tokenized inner expression strings."""
        for expression in expressions:
            validation_error = self._validate_expression(expression.strip())
            if validation_error:
                func_name = validation_error.function_name
                is_strict = False
                if func_name and self._registry.is_strict_conversion(func_name):
                    is_strict = True
                elif self.contains_strict_function(expression):
                    is_strict = True
                    strict_func = next(
                        (
                            fn
                            for fn in self.extract_function_names(expression)
                            if self._registry.is_strict_conversion(fn)
                        ),
                        None,
                    )
                    if strict_func:
                        func_name = strict_func

                if is_strict:
                    logger.debug(
                        "strict_conversion_failure_provenance_detected "
                        "function_name=%s code=%s",
                        func_name or "unknown",
                        validation_error.code or "invalid_syntax",
                    )
                prov = ExpressionFailureProvenance(
                    code=validation_error.code or "invalid_syntax",
                    expression=expression,
                    function_name=func_name,
                    is_strict_conversion=is_strict,
                )
                return ValidationResult.error(
                    validation_error.code or "invalid_syntax",
                    validation_error.function_name,
                    expression,
                    failures=(prov,),
                )

        return ValidationResult.valid()

    def _inspect_single_expression(
        self,
        expr: str,
        span: tuple[int, int] | None = None,
    ) -> ExpressionFailureProvenance | None:
        validation_error = self._validate_expression(expr.strip())
        if validation_error is None:
            return None

        func_name = validation_error.function_name
        is_strict = False
        if func_name and self._registry.is_strict_conversion(func_name):
            is_strict = True
        elif self.contains_strict_function(expr):
            is_strict = True
            strict_func = next(
                (
                    fn
                    for fn in self.extract_function_names(expr)
                    if self._registry.is_strict_conversion(fn)
                ),
                None,
            )
            if strict_func:
                func_name = strict_func

        code = validation_error.code or "invalid_syntax"
        if is_strict:
            logger.debug(
                "strict_conversion_failure_provenance_detected "
                "function_name=%s code=%s span=%s",
                func_name or "unknown",
                code,
                span,
            )
        return ExpressionFailureProvenance(
            code=code,
            expression=expr,
            function_name=func_name,
            is_strict_conversion=is_strict,
            span=span,
        )

    def inspect_failure_provenance(
        self,
        content: str,
        expressions: list[str] | None = None,
    ) -> tuple[ExpressionFailureProvenance, ...]:
        """Inspect content and expressions, returning structured failure provenance."""
        completed_spans: list[tuple[int, int]] = []
        failures: list[ExpressionFailureProvenance] = []

        if expressions is not None:
            for expr in expressions:
                prov = self._inspect_single_expression(expr)
                if prov:
                    failures.append(prov)
        else:
            for match in TEMPLATE_PLACEHOLDER_PATTERN.finditer(content):
                span = match.span()
                completed_spans.append(span)
                expr = match.group(1)
                prov = self._inspect_single_expression(expr, span=span)
                if prov:
                    failures.append(prov)

        if "{{" in content:
            for match in re.finditer(r"\{\{", content):
                start_idx = match.start()
                if any(c_start <= start_idx < c_end for c_start, c_end in completed_spans):
                    continue

                next_delim = content.find("{{", start_idx + 2)
                end_idx = next_delim if next_delim != -1 else len(content)
                unclosed_expr = content[start_idx + 2:end_idx].strip()
                funcs = self.extract_function_names(unclosed_expr)
                func_name: str | None = None
                if funcs:
                    func_name = funcs[0]
                    strict_func = next(
                        (fn for fn in funcs if self._registry.is_strict_conversion(fn)),
                        None,
                    )
                    if strict_func:
                        func_name = strict_func
                        is_strict = True
                    else:
                        is_strict = False
                else:
                    ident_match = self._IDENTIFIER_RE.search(unclosed_expr)
                    first_ident = ident_match.group(1) if ident_match else None
                    func_name = first_ident
                    is_strict = bool(
                        first_ident and self._registry.is_strict_conversion(first_ident)
                    )

                if is_strict:
                    logger.debug(
                        "strict_conversion_failure_provenance_detected "
                        "function_name=%s code=invalid_syntax span=(%d, %d)",
                        func_name or "unknown",
                        start_idx,
                        end_idx,
                    )

                failures.append(
                    ExpressionFailureProvenance(
                        code="invalid_syntax",
                        expression=unclosed_expr,
                        function_name=func_name,
                        is_strict_conversion=is_strict,
                        span=(start_idx, end_idx),
                    )
                )

        return tuple(failures)

    inspect_content_failures = inspect_failure_provenance

    def has_strict_conversion_failure(
        self,
        content: str,
        variables: dict[str, Any] | None = None,
        exc: Exception | None = None,
    ) -> bool:
        """True if content has failed strict conversion statically or in provenance."""
        if isinstance(exc, IntegerConversionError):
            logger.debug(
                "strict_conversion_failure_detected source=exception error_type=%s",
                type(exc).__name__,
            )
            return True
        provenances = self.inspect_failure_provenance(content)
        strict_failure = next((p for p in provenances if p.is_strict_conversion), None)
        if strict_failure is not None:
            logger.debug(
                "strict_conversion_failure_detected source=provenance "
                "function_name=%s code=%s",
                strict_failure.function_name or "unknown",
                strict_failure.code,
            )
            return True
        return False

    def _validate_expression(self, expression: str) -> ValidationResult | None:
        if self._SAFE_PATH_RE.fullmatch(expression):
            return None

        parsed_expression = self._parse_function_expression(expression)
        if isinstance(parsed_expression, ValidationResult):
            return parsed_expression

        function_name, args = parsed_expression
        return self._validate_function_args(function_name, args)

    def _parse_function_expression(
        self,
        expression: str,
    ) -> tuple[str, str] | ValidationResult:
        function_match = self._FUNCTION_SIGNATURE_RE.fullmatch(expression)
        if not function_match:
            return ValidationResult.error("invalid_syntax")

        function_name = function_match.group("func")
        if not self._registry.is_allowed(function_name):
            return ValidationResult.error("unknown_function", function_name)

        return function_name, function_match.group("args").strip()

    def _validate_function_args(
        self,
        function_name: str,
        args: str,
    ) -> ValidationResult | None:
        argument = self._extract_single_argument(args)
        if argument is None:
            return ValidationResult.error("invalid_arity", function_name)

        if self._SAFE_PATH_RE.fullmatch(argument):
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
