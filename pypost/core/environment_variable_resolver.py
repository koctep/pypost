"""Recursive template expression resolver for environment variables (PYPOST-1119)."""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from pypost.core.template_expression_tokenizer import tokenize_template_expressions

if TYPE_CHECKING:
    from pypost.core.template_service import TemplateService

logger = logging.getLogger(__name__)

MAX_VARIABLE_RESOLUTION_DEPTH = 32
_IDENTIFIER_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


def _extract_referenced_keys(template_str: str, available_keys: set[str]) -> set[str]:
    """Extract variable keys referenced in template placeholders."""
    expressions = tokenize_template_expressions(template_str)
    referenced = set()
    for expr in expressions:
        for match in _IDENTIFIER_RE.finditer(expr):
            token = match.group(0)
            if token in available_keys:
                referenced.add(token)
    return referenced


class EnvironmentVariableResolver:
    """Resolves template expressions within environment variable values."""

    def __init__(
        self,
        template_service: TemplateService | None = None,
        max_depth: int = MAX_VARIABLE_RESOLUTION_DEPTH,
    ) -> None:
        self._template_service = template_service
        self._max_depth = max_depth

    def resolve(
        self,
        variables: dict[str, Any],
        render_path: str = "runtime",
    ) -> dict[str, str]:
        """Evaluate template expressions defined within environment profile variables.

        Args:
            variables: Dict of raw variable names and values.
            render_path: Metrics/logging render path identifier ("runtime", "hover", etc.).

        Returns:
            Dict of variable names mapped to their fully resolved string values.
        """
        if not variables:
            return {}

        # Fast path: check if any variable contains '{{'
        raw_map: dict[str, Any] = dict(variables)
        has_template = any(
            isinstance(v, str) and "{{" in v for v in raw_map.values()
        )
        if not has_template:
            return {str(k): str(v) for k, v in raw_map.items()}

        service = self._get_template_service()
        available_keys = {str(k) for k in raw_map}
        resolved_cache: dict[str, str] = {}

        def _resolve_var(name: str, visiting: list[str]) -> str:
            if name not in raw_map:
                return ""

            if name in resolved_cache:
                return resolved_cache[name]

            raw_value = str(raw_map[name])

            # Cycle detection
            if name in visiting:
                cycle_path = " -> ".join(visiting + [name])
                logger.warning(
                    "environment_variable_cycle_detected cycle=%s", cycle_path
                )
                return raw_value

            # Depth limit
            if len(visiting) >= self._max_depth:
                logger.warning(
                    "environment_variable_max_depth_exceeded var=%s depth=%d",
                    name,
                    len(visiting),
                )
                return raw_value

            if "{{" not in raw_value:
                resolved_cache[name] = raw_value
                return raw_value

            new_visiting = visiting + [name]
            referenced = _extract_referenced_keys(raw_value, available_keys)
            context: dict[str, Any] = {}
            for key in referenced:
                context[key] = _resolve_var(key, new_visiting)

            # Include any other non-cyclic, already-resolved variables or static values
            for key, val in raw_map.items():
                if key not in context and key not in new_visiting:
                    if isinstance(val, dict):
                        context[key] = val
                    elif "{{" not in str(val):
                        context[key] = str(val)

            try:
                rendered = service.render_string(
                    raw_value,
                    context,
                    render_path="env_resolve",
                )
                resolved_cache[name] = rendered
                return rendered
            except Exception as exc:
                logger.warning(
                    "environment_variable_resolution_failed var=%s error=%s",
                    name,
                    exc,
                )
                resolved_cache[name] = raw_value
                return raw_value

        result: dict[str, str] = {}
        for key in raw_map:
            result[str(key)] = _resolve_var(str(key), [])

        return result

    def _get_template_service(self) -> TemplateService:
        if self._template_service is not None:
            return self._template_service
        from pypost.core.template_service import TemplateService

        return TemplateService()


def resolve_environment_variables(
    variables: dict[str, Any],
    template_service: TemplateService | None = None,
    render_path: str = "runtime",
) -> dict[str, str]:
    """Convenience function to resolve environment variable templates."""
    return EnvironmentVariableResolver(template_service=template_service).resolve(
        variables, render_path=render_path
    )
