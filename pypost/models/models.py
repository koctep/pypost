import uuid
from typing import Dict, Optional, List
from pydantic import BaseModel, Field


class RequestData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Request"
    method: str = "GET"
    url: str = ""
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)
    body: str = ""
    body_type: str = "json"  # json, text, etc.
    post_script: str = ""  # Python script to execute after response
    expose_as_mcp: bool = False  # Expose this request as an MCP tool

class Collection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Collection"
    requests: List[RequestData] = Field(default_factory=list)

class Environment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Environment"
    variables: Dict[str, str] = Field(default_factory=dict)
    enable_mcp: bool = False


class HistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str                          # UTC ISO-8601, e.g. "2026-03-17T14:30:00.123456Z"
    method: str                             # "GET", "POST", "MCP", …
    url: str                                # resolved URL (after variable substitution)
    headers: Dict[str, str]                 # resolved request headers
    body: str                               # resolved request body
    status_code: int                        # HTTP status code; 0 = network error
    response_time_ms: float                 # round-trip time in milliseconds
    collection_name: Optional[str] = None  # None for ad-hoc requests
    request_name: Optional[str] = None     # None for ad-hoc requests
