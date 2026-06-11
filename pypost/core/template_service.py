import logging
from typing import Any

from jinja2 import Environment

from pypost.core.function_expression_resolver import FunctionExpressionResolver
from pypost.core.function_registry import FunctionRegistry
from pypost.core.metrics import MetricsManager
from pypost.core.template_expression_tokenizer import tokenize_template_expressions
from pypost.core.template_expression_types import ValidationResult

logger = logging.getLogger(__name__)


class TemplateService:
    _VALIDATION_MESSAGES = {
        "unknown_function": "Unknown function: {function_name}",
        "invalid_arity": "Invalid function arity",
        "invalid_argument": "Invalid function argument",
        "invalid_syntax": "Invalid template function expression",
    }

    def __init__(self, metrics: MetricsManager | None = None):
        self.env = Environment()
        self._metrics = metrics
        self._function_registry = FunctionRegistry()
        self._function_registry.register_into_env(self.env)
        self._function_expression_resolver = FunctionExpressionResolver(
            self._function_registry,
        )

    def validate_function_expressions(self, content: str) -> ValidationResult:
        """
        Allow only these placeholder forms:
        - {{identifier}}
        - {{allowed_function(identifier)}}
        - {{allowed_function(nested_func(identifier))}} (recursive allow-list)
        """
        return self._function_expression_resolver.validate_content(content)

    def _validation_message(self, result: ValidationResult) -> str:
        template = self._VALIDATION_MESSAGES.get(
            result.code,
            "Invalid template function expression",
        )
        return template.format(function_name=result.function_name)

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
            self._record_empty_render_attempt(render_path)
            return ""

        expressions = tokenize_template_expressions(content)
        expression_count = len(expressions)
        try:
            validation = self._validate_template_expressions(expressions)
            if not validation.is_valid:
                self._emit_validation_failure_observability(
                    validation,
                    render_path,
                    expression_count,
                )
                raise ValueError(self._validation_message(validation))
            rendered = self._render_with_jinja(content, variables)
            self._emit_render_success_observability(render_path, expression_count)
            return rendered
        except Exception as e:
            return self._fallback_content_after_render_exception(
                e,
                content,
                render_path,
                expression_count,
            )

    def _record_empty_render_attempt(self, render_path: str) -> None:
        if self._metrics:
            self._metrics.track_template_expression_render_attempt(
                render_path=render_path,
                outcome="empty_content",
            )

    def _validate_template_expressions(
        self,
        expressions: list[str],
    ) -> ValidationResult:
        return self._function_expression_resolver.validate_expressions(expressions)

    def _emit_validation_failure_observability(
        self,
        validation: ValidationResult,
        render_path: str,
        expression_count: int,
    ) -> None:
        logger.info(
            "template_expression_validation_failed "
            "render_path=%s code=%s function_name=%s token_count=%d",
            render_path,
            validation.code,
            validation.function_name or "n/a",
            expression_count,
        )
        if self._metrics:
            self._metrics.track_template_expression_render_attempt(
                render_path=render_path,
                outcome="validation_error",
            )
            self._metrics.track_template_expression_validation_failure(
                render_path=render_path,
                code=validation.code or "unknown",
                function_name=validation.function_name,
            )

    def _render_with_jinja(self, content: str, variables: dict[str, Any]) -> str:
        template = self.env.from_string(content)
        return template.render(**variables)

    def _emit_render_success_observability(
        self,
        render_path: str,
        expression_count: int,
    ) -> None:
        if self._metrics:
            self._metrics.track_template_expression_render_attempt(
                render_path=render_path,
                outcome="success",
            )
        logger.debug(
            "template_expression_render_succeeded render_path=%s token_count=%d",
            render_path,
            expression_count,
        )

    def _fallback_content_after_render_exception(
        self,
        exc: Exception,
        content: str,
        render_path: str,
        expression_count: int,
    ) -> str:
        if not isinstance(exc, ValueError) and self._metrics:
            self._metrics.track_template_expression_render_attempt(
                render_path=render_path,
                outcome="render_error",
            )
        logger.warning(
            "template_render_fallback_to_original render_path=%s error_type=%s " "token_count=%d",
            render_path,
            type(exc).__name__,
            expression_count,
        )
        return content

    def parse(self, content: str):
        """
        Parses the content into an AST.
        """
        return self.env.parse(content)
