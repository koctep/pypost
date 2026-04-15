import logging
import re

from jinja2 import Environment

from pypost.core.function_expression_resolver import FunctionExpressionResolver
from pypost.core.function_registry import FunctionRegistry
from pypost.core.metrics import MetricsManager
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
        """
        return self._function_expression_resolver.validate_content(content)

    def _validation_message(self, result: ValidationResult) -> str:
        template = self._VALIDATION_MESSAGES.get(
            result.code,
            "Invalid template function expression",
        )
        return template.format(function_name=result.function_name)

    def render_string(
        self, content: str, variables: dict, render_path: str = "runtime",
    ) -> str:
        """
        Renders a string template with provided variables using Jinja2.

        Args:
            content: The string containing variables like {{ var_name }}
            variables: A dictionary of variable names and values

        Returns:
            The rendered string with variables substituted.
        """
        if not content:
            if self._metrics:
                self._metrics.track_template_expression_render_attempt(
                    render_path=render_path, outcome="empty_content",
                )
            return ""

        expression_count = len(re.findall(r"\{\{\s*(.*?)\s*\}\}", content))
        try:
            validation = self._function_expression_resolver.validate_content(content)
            if not validation.is_valid:
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
                        render_path=render_path, outcome="validation_error",
                    )
                    self._metrics.track_template_expression_validation_failure(
                        render_path=render_path,
                        code=validation.code or "unknown",
                        function_name=validation.function_name,
                    )
                raise ValueError(self._validation_message(validation))
            template = self.env.from_string(content)
            rendered = template.render(**variables)
            if self._metrics:
                self._metrics.track_template_expression_render_attempt(
                    render_path=render_path, outcome="success",
                )
            logger.debug(
                "template_expression_render_succeeded render_path=%s token_count=%d",
                render_path,
                expression_count,
            )
            return rendered
        except ValueError:
            logger.warning(
                "template_render_fallback_to_original render_path=%s error_type=%s "
                "token_count=%d",
                render_path,
                "ValueError",
                expression_count,
            )
            return content
        except Exception as e:
            if self._metrics:
                self._metrics.track_template_expression_render_attempt(
                    render_path=render_path, outcome="render_error",
                )
            logger.warning(
                "template_render_fallback_to_original render_path=%s error_type=%s "
                "token_count=%d",
                render_path,
                type(e).__name__,
                expression_count,
            )
            return content

    def parse(self, content: str):
        """
        Parses the content into an AST.
        """
        return self.env.parse(content)
