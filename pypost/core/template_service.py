from __future__ import annotations

from functools import lru_cache
import re
from typing import Any

from jinja2 import Environment

from pypost.core.function_expression_resolver import FunctionExpressionResolver
from pypost.core.function_registry import FunctionRegistry
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.template_expression_tokenizer import (
    TEMPLATE_PLACEHOLDER_PATTERN,
    tokenize_template_expressions,
)
from pypost.core.template_expression_types import IntegerConversionError, ValidationResult
from pypost.core.template_service_render import (
    emit_render_success_observability,
    emit_validation_failure_observability,
    fallback_content_after_render_exception,
    record_empty_render_attempt,
    render_with_jinja,
    validation_message,
)


class TemplateService:
    """Central ``{{...}}`` substitution entry point (PYPOST-18).

    Autonomous-default (PYPOST-45): ``HTTPClient``, ``RequestService``, and
    ``MCPServerImpl`` accept optional ``template_service``. When omitted or
    ``None``, each creates ``TemplateService()`` locally — no module singleton.
    ``main.py`` injects one instance through the UI/MCP chain for a shared
    Jinja2 ``Environment``; isolated callers get separate envs (cheap, intentional).
    See ``doc/dev/template_service.md`` for consumers and test seams.
    """

    # Only a direct ``to_int`` placeholder participates in strict conversion;
    # ``not_to_int(...)`` and ``value.to_int(...)`` remain unrelated forms.
    _DIRECT_TO_INT_CALL_RE = re.compile(r"^\s*to_int\s*\(")
    _STARTED_TO_INT_CALL_RE = re.compile(r"\{\{\s*to_int\s*\(")

    def __init__(self, metrics: MetricsTrackerProtocol | None = None):
        self.env = Environment()
        self._metrics = resolve_metrics(metrics)
        self._function_registry = FunctionRegistry()
        self._function_registry.register_into_env(self.env)
        self._function_expression_resolver = FunctionExpressionResolver(
            self._function_registry,
        )

        @lru_cache(maxsize=256)
        def _compile_template(content: str):
            return self.env.from_string(content)

        self._compile_template = _compile_template

    def validate_function_expressions(self, content: str) -> ValidationResult:
        """
        Allow only these placeholder forms:
        - {{identifier}}
        - {{allowed_function(identifier)}}
        - {{allowed_function(nested_func(identifier))}} (recursive allow-list)
        """
        return self._function_expression_resolver.validate_content(content)

    def render_string(
        self,
        content: str,
        variables: dict[str, Any],
        render_path: str = "runtime",
        *,
        strict_conversion: bool = False,
    ) -> str:
        """
        Renders a string template with provided variables using Jinja2.

        Orchestration stages:
        1. Empty content: record empty_content attempt when metrics exist; return "".
        2. Count `{{ ... }}` placeholders for logs and metrics.
        3. Validate function-style placeholders via the resolver.
        4. If invalid: validation observability; raise ValueError inside the try (caught
           below; original content is returned).
        5. Build template and render with Jinja; on success, record success observability.
        6. On any Exception inside the try (including that ValueError): warning log; for
           non-ValueError, record render_error when metrics exist; return original content.

        Args:
            content: The string containing variables like {{ var_name }}
            variables: A dictionary of variable names and values

        Returns:
            The rendered string with variables substituted.
        """
        if not content:
            record_empty_render_attempt(self._metrics, render_path)
            return ""

        expressions = tokenize_template_expressions(content)
        expression_count = len(expressions)
        validation: ValidationResult | None = None
        try:
            validation = self._validate_template_expressions(expressions)
            if not validation.is_valid:
                emit_validation_failure_observability(
                    self._metrics,
                    validation,
                    render_path,
                    expression_count,
                )
                raise ValueError(validation_message(validation))
            rendered = render_with_jinja(
                self._compile_template,
                content,
                variables,
                self._metrics,
                render_path,
            )
            emit_render_success_observability(
                self._metrics,
                render_path,
                expression_count,
            )
            return rendered
        except Exception as exc:
            fallback = fallback_content_after_render_exception(
                self._metrics,
                exc,
                content,
                render_path,
                expression_count,
            )
            if strict_conversion and self._is_failed_to_int_expression(
                content,
                exc,
                variables,
            ):
                if isinstance(exc, IntegerConversionError):
                    raise
                raise IntegerConversionError("Invalid to_int template expression") from exc
            return fallback

    def _is_failed_to_int_expression(
        self,
        content: str,
        exc: Exception,
        variables: dict[str, Any],
    ) -> bool:
        """Identify failed direct ``to_int`` expressions without widening fallback.

        A field can contain more than one placeholder.  The normal resolver
        intentionally stops at the first invalid one, so its provenance alone
        cannot tell us whether a later direct ``to_int`` also failed.  Inspect
        each direct call independently only after the ordinary render has
        failed.  This preserves literal fallback when there is no failed
        ``to_int`` call, including a valid conversion beside an unrelated
        invalid expression.
        """
        if isinstance(exc, IntegerConversionError):
            return True

        completed_direct_calls: list[tuple[int, int]] = []
        for token in TEMPLATE_PLACEHOLDER_PATTERN.finditer(content):
            expression = token.group(1)
            if not self._DIRECT_TO_INT_CALL_RE.search(expression):
                continue
            completed_direct_calls.append(token.span())

            expression_validation = self._validate_template_expressions([expression])
            if not expression_validation.is_valid:
                return True

            try:
                self._compile_template("{{" + expression + "}}").render(variables)
            except IntegerConversionError:
                return True

        # An unclosed ``{{to_int(...`` placeholder is not tokenized by the
        # legacy tokenizer and reaches Jinja as a syntax error.  Do not mistake
        # a completed, valid call earlier in the field for that malformed form.
        return any(
            not any(start <= match.start() < end for start, end in completed_direct_calls)
            for match in self._STARTED_TO_INT_CALL_RE.finditer(content)
        )

    def render_string_strict_conversion(
        self,
        content: str,
        variables: dict[str, Any],
        render_path: str = "http",
    ) -> str:
        """Render for HTTP preparation, propagating only failed ``to_int`` calls.

        First render through the base strict path to fail closed for invalid
        conversions, then let an injected subclass provide the final rendering.
        The latter preserves the established ``render_string(content,
        variables)`` injection seam, including legacy overrides that do not
        accept the new keyword-only strict mode.
        """
        base_rendered = TemplateService.render_string(
            self,
            content,
            variables,
            render_path,
            strict_conversion=True,
        )
        if type(self).render_string is TemplateService.render_string:
            return base_rendered
        return self.render_string(content, variables)

    def _validate_template_expressions(
        self,
        expressions: list[str],
    ) -> ValidationResult:
        return self._function_expression_resolver.validate_expressions(expressions)

    def parse(self, content: str):
        """
        Parses the content into an AST.
        """
        return self.env.parse(content)
