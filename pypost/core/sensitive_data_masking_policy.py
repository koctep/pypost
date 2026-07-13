from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Set

from pypost.core.http_client import ResolvedRequestFields
from pypost.core.sensitive_text_sanitizer import HIDDEN_PLACEHOLDER, sanitize_headers, sanitize_text
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData


@dataclass(frozen=True)
class MaskedRequestData:
    url: str
    headers: Dict[str, str]
    body: str


class SensitiveDataMaskingPolicy:
    """Builds history-safe request fields with hidden-key and heuristic redaction."""

    def __init__(self, template_service: TemplateService) -> None:
        self._template_service = template_service

    def build_history_safe_fields(
        self,
        request: RequestData,
        variables: Mapping[str, Any],
        hidden_keys: Set[str] | None = None,
        resolved: ResolvedRequestFields | None = None,
    ) -> MaskedRequestData:
        hidden = hidden_keys or set()
        env_vars = {k: str(v) for k, v in variables.items()}

        if hidden:
            if resolved is not None:
                rendered = MaskedRequestData(
                    url=resolved.url,
                    headers=dict(resolved.headers),
                    body=resolved.body,
                )
            else:
                masked_variables = dict(variables)
                for key in hidden:
                    if key in masked_variables:
                        masked_variables[key] = HIDDEN_PLACEHOLDER
                rendered = MaskedRequestData(
                    url=self._template_service.render_string(
                        request.url, masked_variables
                    ),
                    headers={
                        self._template_service.render_string(
                            k, masked_variables
                        ): self._template_service.render_string(v, masked_variables)
                        for k, v in request.headers.items()
                    },
                    body=self._template_service.render_string(
                        request.body, masked_variables
                    ),
                )
        elif resolved is not None:
            rendered = MaskedRequestData(
                url=resolved.url,
                headers=dict(resolved.headers),
                body=resolved.body,
            )
        else:
            rendered = MaskedRequestData(
                url=self._template_service.render_string(request.url, variables),
                headers={
                    self._template_service.render_string(k, variables): (
                        self._template_service.render_string(v, variables)
                    )
                    for k, v in request.headers.items()
                },
                body=self._template_service.render_string(request.body, variables),
            )

        if hidden:
            safe_headers = {
                key: sanitize_text(value, env_vars=env_vars, hidden_keys=hidden)
                for key, value in rendered.headers.items()
            }
        else:
            safe_headers = sanitize_headers(
                rendered.headers, env_vars=env_vars, hidden_keys=hidden
            )

        return MaskedRequestData(
            url=sanitize_text(rendered.url, env_vars=env_vars, hidden_keys=hidden),
            headers=safe_headers,
            body=sanitize_text(rendered.body, env_vars=env_vars, hidden_keys=hidden),
        )
