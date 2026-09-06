from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from pypost.models.collection_variable import CollectionVariable
from pypost.models.retry import RetryPolicy
from pypost.models.mcp_client import McpClientConnection
from pypost.models.websocket import WebSocketConnection

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


class LibraryCollectionLink(BaseModel):
    """Source metadata for an active collection imported in Link mode.

    ``collection_path`` is always relative to the connected library root.  The
    import service is responsible for validating and normalizing it before a
    link is created; keeping this model free of filesystem access makes it safe
    to persist and use in non-Qt code.
    """

    library_id: str
    manifest_id: Optional[str] = None
    collection_path: str
    collection_index: Optional[int] = None

    @property
    def source_path(self) -> str:
        """Compatibility name for callers that call the entry a source path."""
        return self.collection_path

    @property
    def manifest_path(self) -> str:
        """Return the normalized path recorded in the library manifest."""
        return self.collection_path


class Collection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Collection"
    description: str = ""
    version: str = "1.0.0"
    variables: List[CollectionVariable] = Field(default_factory=list)
    presets: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    requests: List[RequestData] = Field(default_factory=list)
    websockets: List[WebSocketConnection] = Field(default_factory=list)
    mcp_clients: List[McpClientConnection] = Field(default_factory=list)
    # ``exclude_if`` keeps legacy Copy JSON stable while retaining Link
    # metadata whenever it is present.
    library_link: Optional[LibraryCollectionLink] = Field(
        default=None, exclude_if=lambda value: value is None
    )


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


WebSocketConnection.model_rebuild(_types_namespace={"McpToolParam": McpToolParam})
