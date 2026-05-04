from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Set

from pypost.models.models import RequestData
from pypost.core.template_service import TemplateService

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
    ) -> MaskedRequestData:
        masked_variables = dict(variables)
        for key in hidden_keys or set():
            if key in masked_variables:
                masked_variables[key] = HIDDEN_PLACEHOLDER

        return MaskedRequestData(
            url=self._template_service.render_string(request.url, masked_variables),
            headers={
                self._template_service.render_string(k, masked_variables):
                self._template_service.render_string(v, masked_variables)
                for k, v in request.headers.items()
            },
            body=self._template_service.render_string(request.body, masked_variables),
        )
