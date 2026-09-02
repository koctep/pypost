from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from jinja2 import Environment

from pypost.core.environment_variable_resolver import EnvironmentVariableResolver
from pypost.core.function_expression_resolver import FunctionExpressionResolver
from pypost.core.function_registry import FunctionRegistry
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.template_expression_tokenizer import (
    lex_template_expressions,
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


logger = logging.getLogger(__name__)


class TemplateService:
    """Central ``{{...}}`` substitution entry point (PYPOST-18).

    Accepts optional ``template_service`` across client/service layer.
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
        """Validate placeholder forms against allowed function expressions."""
        return self._function_expression_resolver.validate_content(content)

    def resolve_environment_variables(
        self,
        variables: dict[str, Any],
        render_path: str = "runtime",
    ) -> dict[str, str]:
        """Evaluate template expressions defined in environment variables (PYPOST-1119)."""
        return EnvironmentVariableResolver(self).resolve(
            variables,
            render_path=render_path,
        )

    def render_string(
        self,
        content: str,
        variables: dict[str, Any],
        render_path: str = "runtime",
        *,
        strict_conversion: bool = False,
    ) -> str:
        """Renders a string template with provided variables using Jinja2."""
        if not content:
            record_empty_render_attempt(self._metrics, render_path)
            return ""

        if render_path != "env_resolve" and variables and any(
            isinstance(v, str) and "{{" in v for v in variables.values()
        ):
            variables = self.resolve_environment_variables(
                variables, render_path=render_path
            )

        template_tokens = lex_template_expressions(content)
        expressions = [token.expression for token in template_tokens if token.closed]
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
            if strict_conversion and self._contains_failed_to_int_call(
                content, exc, variables, template_tokens
            ):
                logger.info(
                    "strict_conversion_failure_propagated render_path=%s error_type=%s",
                    render_path,
                    type(exc).__name__,
                )
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
        """Backward-compatibility wrapper for _contains_failed_to_int_call."""
        return self._contains_failed_to_int_call(content, exc, variables)

    def _contains_failed_to_int_call(
        self,
        content: str,
        exc: Exception,
        variables: dict[str, Any],
        template_tokens: tuple[Any, ...] | None = None,
    ) -> bool:
        """Identify failed strict conversion expressions without widening fallback.

        Relies on FunctionExpressionResolver structured failure provenance and
        dynamic evaluation of strict expressions.
        """
        if isinstance(exc, IntegerConversionError):
            logger.debug(
                "strict_conversion_failure_identified source=exception error_type=%s",
                type(exc).__name__,
            )
            return True

        # Check structured failure provenance from the resolver (syntax errors,
        # unclosed placeholders, arity errors, unknown functions in strict context).
        provenances = self._function_expression_resolver.inspect_failure_provenance(
            content, tokens=template_tokens
        )
        strict_prov = next((p for p in provenances if p.is_strict_conversion), None)
        if strict_prov is not None:
            logger.debug(
                "strict_conversion_failure_identified source=provenance "
                "function_name=%s code=%s",
                strict_prov.function_name or "unknown",
                strict_prov.code,
            )
            return True

        # Evaluate all valid strict placeholders in one cached template. This keeps the
        # fallback path linear in the number of placeholders and avoids one Jinja compile
        # and render call per placeholder.
        tokens = (
            template_tokens
            if template_tokens is not None
            else lex_template_expressions(content)
        )
        strict_expressions: list[str] = []
        for token in tokens:
            if not token.closed:
                continue
            expression = token.expression
            if not self._function_expression_resolver.contains_strict_function(expression):
                continue

            expression_validation = self._validate_template_expressions([expression])
            if not expression_validation.is_valid:
                logger.debug(
                    "strict_conversion_failure_identified source=validation "
                    "function_name=%s code=%s",
                    expression_validation.function_name or "unknown",
                    expression_validation.code or "unknown",
                )
                return True

            strict_expressions.append(expression)

        if not strict_expressions:
            return False

        try:
            strict_template = "".join(
                "{{" + expression + "}}" for expression in strict_expressions
            )
            self._compile_template(strict_template).render(**variables)
        except IntegerConversionError as conv_err:
            logger.debug(
                "strict_conversion_failure_identified source=eval error_type=%s",
                type(conv_err).__name__,
            )
            return True
        except Exception:
            pass

        return False

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
