from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from pypost.models.retry import RetryPolicy

_MCP_PARAM_TYPES = frozenset(
    {"string", "integer", "integer_or_string", "number", "boolean", "array", "object"}
)


class McpToolParam(BaseModel):
    """Agent-visible metadata for one MCP tool parameter."""

    type: str = "string"
    description: str = ""
    required: bool = True
    default: Optional[Any] = None

    def model_post_init(self, __context) -> None:
        if self.type not in _MCP_PARAM_TYPES:
            raise ValueError(f"Unsupported MCP param type: {self.type}")
        self._validate_default_type()

    def _validate_default_type(self) -> None:
        """Validate that ``self.default`` is compatible with ``self.type``.

        ``None`` is always permitted (no default set).  Any mismatch raises
        ``ValueError`` which Pydantic converts to ``ValidationError``.
        """
        if self.default is None:
            return

        value = self.default
        param_type = self.type

        type_ok: bool
        if param_type == "string":
            type_ok = isinstance(value, str)
        elif param_type == "integer":
            type_ok = isinstance(value, int) and not isinstance(value, bool)
        elif param_type == "integer_or_string":
            type_ok = isinstance(value, (int, str)) and not isinstance(value, bool)
        elif param_type == "number":
            type_ok = isinstance(value, (int, float)) and not isinstance(value, bool)
        elif param_type == "boolean":
            type_ok = isinstance(value, bool)
        elif param_type == "array":
            type_ok = isinstance(value, list)
        elif param_type == "object":
            type_ok = isinstance(value, dict)
        else:
            # Unknown type — whitelist check above already rejected it; be safe.
            type_ok = True

        if not type_ok:
            raise ValueError(
                f"default value {value!r} is not valid for param type {param_type!r}"
            )


class RequestData(BaseModel):
    """In-memory request draft for the editor and collection persistence.

    Keep this model lean: editor fields and metadata only. Do not attach HTTP
    response bodies, history entries, or other large runtime buffers — those
    belong in ``ResponseView`` and ``HistoryManager``. Tab isolation deep-copies
    ``RequestData``; heavier payloads would amplify copy cost (see
    ``doc/dev/request_data_copy_policy.md``).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Request"
    method: str = "GET"
    url: str = ""
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)
    body: str = ""
    body_type: str = "json"  # json, text, etc.
    yaml_as_json: bool = False
    post_script: str = ""  # Python script to execute after response
    expose_as_mcp: bool = False  # Expose this request as an MCP tool
    mcp_description: str = ""  # Agent-visible tool description (falls back to name)
    mcp_params: Dict[str, McpToolParam] = Field(default_factory=dict)
    retry_policy: Optional[RetryPolicy] = None


class Collection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Collection"
    requests: List[RequestData] = Field(default_factory=list)


class Environment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Environment"
    variables: Dict[str, str] = Field(default_factory=dict)
    hidden_keys: Set[str] = Field(default_factory=set)
    enable_mcp: bool = False


class HistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str  # UTC ISO-8601, e.g. "2026-03-17T14:30:00.123456Z"
    method: str  # "GET", "POST", "MCP", …
    url: str  # resolved URL (after variable substitution)
    headers: Dict[str, str]  # resolved request headers
    body: str  # resolved request body
    status_code: int  # HTTP status code; 0 = network error
    response_time_ms: float  # round-trip time in milliseconds
    collection_name: Optional[str] = None  # None for ad-hoc requests
    request_name: Optional[str] = None  # None for ad-hoc requests
