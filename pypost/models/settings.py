from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from pypost.models.retry import RetryPolicy
from pypost.models.websocket import HeartbeatPolicy, ReconnectPolicy

ThemeSetting = Literal["system", "light", "dark"]


class McpServerConfiguration(BaseModel):
    """One independently managed, persisted MCP endpoint."""

    id: str
    name: Optional[str] = None
    host: str = "127.0.0.1"
    port: int = Field(ge=1024, le=65535)
    collection_id: Optional[str] = None
    environment_id: str
    server_type: Literal["local", "proxy"] = "local"
    upstream_url: Optional[str] = None
    upstream_transport: Literal["streamable_http", "sse"] = "streamable_http"
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: float = 30.0
    enabled: bool = False

    @model_validator(mode="after")
    def validate_server_type_requirements(self) -> "McpServerConfiguration":
        if self.server_type == "proxy":
            if not self.upstream_url or not self.upstream_url.strip():
                raise ValueError("Proxy MCP server requires a non-empty upstream_url")
        elif self.server_type == "local":
            if not self.collection_id or not self.collection_id.strip():
                raise ValueError("Local MCP server requires a non-empty collection_id")
        return self


class AppSettings(BaseModel):
    font_size: int = 12
    indent_size: int = 2
    theme: ThemeSetting = "system"
    request_timeout: int = 60
    config_version: int = 1
    revision: int = 0
    last_environment_id: Optional[str] = None
    open_tabs: List[str] = []
    expanded_collections: List[str] = []
    confirm_overwrite_request: bool = False
    mcp_port: int = 1080
    mcp_host: str = "127.0.0.1"
    mcp_servers: List[McpServerConfiguration] = []
    metrics_port: int = 9080
    metrics_host: str = "127.0.0.1"
    default_retry_policy: Optional[RetryPolicy] = None
    alert_webhook_url: Optional[str] = None
    alert_webhook_auth_header: Optional[str] = None
    alert_log_path: Optional[str] = None
    log_level: str = "INFO"
    log_hidden_key_names: bool = False
    env_encryption_enabled: Optional[bool] = None
    env_encryption_key_source: Optional[str] = None
    env_encryption_key_source_fallback: Optional[List[str]] = None
    max_response_bytes: int = 52_428_800
    ws_max_stream_entries: int = 5_000
    ws_session_memory_budget_bytes: int = 67_108_864
    ws_max_incoming_message_bytes: int = 8_388_608
    ws_display_truncate_bytes: int = 262_144
    ws_default_heartbeat: HeartbeatPolicy = Field(default_factory=HeartbeatPolicy)
    ws_default_reconnect: ReconnectPolicy = Field(default_factory=ReconnectPolicy)
    ws_mcp_probe_max_messages: int = 10
    ws_mcp_probe_max_duration_ms: int = 10_000
    ws_max_concurrent_sessions: int = 8

    @model_validator(mode="after")
    def validate_mcp_server_ports(self) -> "AppSettings":
        """Ports identify MCP endpoints globally, irrespective of bind host."""
        ports = [server.port for server in self.mcp_servers]
        if len(ports) != len(set(ports)):
            raise ValueError("MCP server configurations must use unique ports")
        return self
