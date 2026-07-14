"""Private render and observability helpers for ``TemplateService`` (PYPOST-700)."""

import logging
import time
from collections.abc import Callable
from typing import Any

from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.template_expression_types import ValidationResult

logger = logging.getLogger(__name__)

VALIDATION_MESSAGES = {
    "unknown_function": "Unknown function: {function_name}",
    "invalid_arity": "Invalid function arity",
    "invalid_argument": "Invalid function argument",
    "invalid_syntax": "Invalid template function expression",
}


def validation_message(result: ValidationResult) -> str:
    template = VALIDATION_MESSAGES.get(
        result.code,
        "Invalid template function expression",
    )
    return template.format(function_name=result.function_name)


def record_empty_render_attempt(
    metrics: MetricsTrackerProtocol,
    render_path: str,
) -> None:
    metrics.track_template_expression_render_attempt(
        render_path=render_path,
        outcome="empty_content",
    )


def emit_validation_failure_observability(
    metrics: MetricsTrackerProtocol,
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
    metrics.track_template_expression_render_attempt(
        render_path=render_path,
        outcome="validation_error",
    )
    metrics.track_template_expression_validation_failure(
        render_path=render_path,
        code=validation.code or "unknown",
        function_name=validation.function_name,
    )


def render_with_jinja(
    compile_template: Callable[[str], Any],
    content: str,
    variables: dict[str, Any],
    metrics: MetricsTrackerProtocol,
    render_path: str,
) -> str:
    start = time.perf_counter()
    try:
        template = compile_template(content)
        if logger.isEnabledFor(logging.DEBUG):
            info = compile_template.cache_info()
            logger.debug(
                "template_compile_cache hits=%d misses=%d size=%d",
                info.hits,
                info.misses,
                info.currsize,
            )
        return template.render(**variables)
    finally:
        metrics.track_template_expression_render_duration(
            render_path,
            time.perf_counter() - start,
        )


def emit_render_success_observability(
    metrics: MetricsTrackerProtocol,
    render_path: str,
    expression_count: int,
) -> None:
    metrics.track_template_expression_render_attempt(
        render_path=render_path,
        outcome="success",
    )
    logger.debug(
        "template_expression_render_succeeded render_path=%s token_count=%d",
        render_path,
        expression_count,
    )


def fallback_content_after_render_exception(
    metrics: MetricsTrackerProtocol,
    exc: Exception,
    content: str,
    render_path: str,
    expression_count: int,
) -> str:
    if not isinstance(exc, ValueError):
        metrics.track_template_expression_render_attempt(
            render_path=render_path,
            outcome="render_error",
        )
    logger.warning(
        "template_render_fallback_to_original render_path=%s error_type=%s "
        "token_count=%d",
        render_path,
        type(exc).__name__,
        expression_count,
    )
    return content
