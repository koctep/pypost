from pydantic import BaseModel

from typing import Optional, List

from pypost.models.retry import RetryPolicy


class AppSettings(BaseModel):
    font_size: int = 12
    indent_size: int = 2
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
    metrics_host: str = "0.0.0.0"
    default_retry_policy: Optional[RetryPolicy] = None
    alert_webhook_url: Optional[str] = None
    alert_webhook_auth_header: Optional[str] = None
    alert_log_path: Optional[str] = None

