import logging
import base64
import hashlib
import re
from dataclasses import dataclass
from urllib.parse import quote
from jinja2 import Environment
from pypost.core.metrics import MetricsManager

logger = logging.getLogger(__name__)


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


class TemplateService:
    _ALLOWED_FUNCTIONS = {"urlencode", "md5", "base64"}
    _IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    _FUNCTION_SIGNATURE_RE = re.compile(
        r"^(?P<func>[a-zA-Z_][a-zA-Z0-9_]*)\((?P<args>.*)\)$"
    )
    _VALIDATION_MESSAGES = {
        "unknown_function": "Unknown function: {function_name}",
        "invalid_arity": "Invalid function arity",
        "invalid_argument": "Invalid function argument",
        "invalid_syntax": "Invalid template function expression",
    }

    def __init__(self, metrics: MetricsManager | None = None):
        self.env = Environment()
        self._metrics = metrics
        self._register_allowed_functions()

    def _register_allowed_functions(self) -> None:
        """
        Register only approved template-callable functions.
        """
        self.env.globals.update({
            "urlencode": self._urlencode,
            "md5": self._md5,
            "base64": self._base64_encode,
        })

    @staticmethod
    def _urlencode(value) -> str:
        """
        URL-encode a value for safe usage in paths/query.
        """
        return quote(str(value), safe="")

    @staticmethod
    def _md5(value) -> str:
        """
        Return hex MD5 digest of the provided value.
        """
        raw = str(value).encode("utf-8")
        return hashlib.md5(raw).hexdigest()

    @staticmethod
    def _base64_encode(value) -> str:
        """
        Return Base64-encoded string for the provided value.
        """
        raw = str(value).encode("utf-8")
        return base64.b64encode(raw).decode("utf-8")

    def validate_function_expressions(self, content: str) -> ValidationResult:
        """
        Allow only these placeholder forms:
        - {{identifier}}
        - {{allowed_function(identifier)}}
        """
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
        if function_name not in self._ALLOWED_FUNCTIONS:
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
            validation = self.validate_function_expressions(content)
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
