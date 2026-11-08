from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from pypost.models.retry import RetryPolicy
from pypost.models.websocket import HeartbeatPolicy, ReconnectPolicy

ThemeSetting = Literal["system", "light", "dark"]


class McpResourceLimitsPolicy(BaseModel):
    """Memory ceilings and spawn admission policy for isolated MCP workers."""

    max_process_workers: int = Field(default=0, ge=0, le=100)
    max_total_rss_mb: float = Field(default=0.0, ge=0.0)
    soft_memory_limit_mb: float = Field(default=0.0, ge=0.0)
    hard_memory_limit_mb: float = Field(default=0.0, ge=0.0)
    memory_sample_interval_s: float = Field(default=1.0, gt=0.0)
    default_worker_rss_estimate_mb: float = Field(default=50.0, ge=0.0)

    @model_validator(mode="after")
    def validate_memory_limits(self) -> "McpResourceLimitsPolicy":
        if self.hard_memory_limit_mb > 0.0 and self.soft_memory_limit_mb > 0.0:
            if self.hard_memory_limit_mb < self.soft_memory_limit_mb:
                raise ValueError(
                    "hard_memory_limit_mb cannot be less than soft_memory_limit_mb"
                )
        return self


class McpWorkerRestartPolicy(BaseModel):
    """Progressive exponential backoff restart policy for isolated MCP workers."""

    enabled: bool = False
    max_retries: int = Field(default=3, ge=0, le=100)
    initial_backoff_s: float = Field(default=0.5, gt=0.0)
    max_backoff_s: float = Field(default=8.0, gt=0.0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0)
    healthy_reset_window_s: float = Field(default=30.0, ge=0.0)

    @model_validator(mode="after")
    def validate_backoff_bounds(self) -> "McpWorkerRestartPolicy":
        if self.max_backoff_s < self.initial_backoff_s:
            raise ValueError("max_backoff_s cannot be less than initial_backoff_s")
        return self

    def backoff_for_attempt(self, attempt: int) -> float:
        if attempt <= 1:
            return min(self.max_backoff_s, self.initial_backoff_s)
        delay = self.initial_backoff_s * (self.backoff_multiplier ** (attempt - 1))
        return min(self.max_backoff_s, delay)


class McpServerConfiguration(BaseModel):
    """One independently managed, persisted MCP endpoint."""

    id: str
    name: Optional[str] = None
    host: str = "127.0.0.1"
    port: int = Field(ge=1024, le=65535)
    collection_id: Optional[str] = None
    library_id: Optional[str] = None
    manifest_id: Optional[str] = None
    library_collection_path: Optional[str] = None
    library_collection_index: Optional[int] = None
    environment_id: Optional[str] = None
    server_type: Literal["local", "proxy"] = "local"
    upstream_url: Optional[str] = None
    upstream_transport: Literal["streamable_http", "sse"] = "streamable_http"
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: float = 30.0
    enabled: bool = False
    bundled_library: bool = False

    @model_validator(mode="after")
    def validate_server_type_requirements(self) -> "McpServerConfiguration":
        if self.server_type == "proxy":
            if not self.upstream_url or not self.upstream_url.strip():
                raise ValueError("Proxy MCP server requires a non-empty upstream_url")
        elif self.server_type == "local":
            if self.library_id:
                required = (self.manifest_id, self.library_collection_path)
                if not all(value and str(value).strip() for value in required):
                    raise ValueError(
                        "Library MCP server requires manifest and collection identity"
                    )
                if self.bundled_library and self.library_id != "pypost-examples":
                    raise ValueError(
                        "bundled_library requires library_id 'pypost-examples'"
                    )
            elif self.bundled_library:
                raise ValueError("bundled_library requires library_id")
            elif not self.collection_id or not self.collection_id.strip():
                raise ValueError("Local MCP server requires a non-empty collection_id")
            elif not self.environment_id or not self.environment_id.strip():
                raise ValueError("Workspace local MCP server requires a non-empty environment_id")
        return self

    @property
    def library_selection(self) -> dict[str, object] | None:
        """Return the stable library identity without exposing mutable model state."""
        if not self.library_id:
            return None
        return {
            "library_id": self.library_id,
            "manifest_id": self.manifest_id,
            "path": self.library_collection_path,
            "index": self.library_collection_index,
        }


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
    mcp_execution_mode: Literal["thread", "process"] = "thread"
    mcp_restart_policy: McpWorkerRestartPolicy = Field(
        default_factory=McpWorkerRestartPolicy
    )
    mcp_resource_limits: McpResourceLimitsPolicy = Field(
        default_factory=McpResourceLimitsPolicy
    )
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
