"""Helpers for comparing persisted request fields across isolated tabs.

Copy policy
-----------

Tab isolation uses deep copies of ``RequestData`` so each tab owns its draft.
Call :func:`copy_request_for_isolated_tab` at tab boundaries (Collections emit,
``add_new_tab``, ``restore_tabs``). ``RequestData`` must stay lean — editor and
persistence fields only; response bodies and history live in ``ResponseView`` /
``HistoryManager``, not in the model. See ``doc/dev/request_data_copy_policy.md``.
"""

from __future__ import annotations

from pypost.models.models import RequestData

_PERSISTED_FIELD_NAMES = (
    "name",
    "url",
    "method",
    "headers",
    "params",
    "body",
    "body_type",
    "yaml_as_json",
    "post_script",
    "expose_as_mcp",
    "mcp_description",
    "mcp_params",
    "retry_policy",
)


def copy_request_for_isolated_tab(data: RequestData) -> RequestData:
    """Return a deep copy of *data* for isolated tab ownership.

    Centralizes ``model_copy(deep=True)`` so tab-isolation semantics stay in one
    place. Cost scales with editor field size (headers, params, body); keep
    ``RequestData`` free of large response buffers.
    """
    return data.model_copy(deep=True)


def snapshot_persisted_fields(data: RequestData) -> RequestData:
    """Return a deep copy used as the persisted-field baseline for a tab."""
    return copy_request_for_isolated_tab(data)


def persisted_fields_equal(a: RequestData, b: RequestData) -> bool:
    """Return True when two requests match on all persisted editor fields."""
    for field_name in _PERSISTED_FIELD_NAMES:
        if getattr(a, field_name) != getattr(b, field_name):
            return False
    return True
