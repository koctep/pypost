from __future__ import annotations

from functools import lru_cache
from typing import Any

from jinja2 import Environment

from pypost.core.function_expression_resolver import FunctionExpressionResolver
from pypost.core.function_registry import FunctionRegistry
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.template_expression_tokenizer import tokenize_template_expressions
from pypost.core.template_expression_types import ValidationResult
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
        except Exception as e:
            return fallback_content_after_render_exception(
                self._metrics,
                e,
                content,
                render_path,
                expression_count,
            )

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
