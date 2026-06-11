from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Set

from pypost.core.http_client import ResolvedRequestFields
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData

HIDDEN_PLACEHOLDER = "***"


@dataclass(frozen=True)
class MaskedRequestData:
    url: str
    headers: Dict[str, str]
    body: str


class SensitiveDataMaskingPolicy:
    """Builds history-safe request fields when hidden env values are involved."""

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
        if hidden:
            masked_variables = dict(variables)
            for key in hidden:
                if key in masked_variables:
                    masked_variables[key] = HIDDEN_PLACEHOLDER
            return MaskedRequestData(
                url=self._template_service.render_string(request.url, masked_variables),
                headers={
                    self._template_service.render_string(
                        k, masked_variables
                    ): self._template_service.render_string(v, masked_variables)
                    for k, v in request.headers.items()
                },
                body=self._template_service.render_string(request.body, masked_variables),
            )
        if resolved is not None:
            return MaskedRequestData(
                url=resolved.url,
                headers=dict(resolved.headers),
                body=resolved.body,
            )
        return MaskedRequestData(
            url=self._template_service.render_string(request.url, variables),
            headers={
                self._template_service.render_string(k, variables): self._template_service.render_string(
                    v, variables
                )
                for k, v in request.headers.items()
            },
            body=self._template_service.render_string(request.body, variables),
        )
