import uuid
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field

from pypost.models.retry import RetryPolicy


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
