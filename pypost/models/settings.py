from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel

from pypost.models.retry import RetryPolicy

ThemeSetting = Literal["system", "light", "dark"]


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
