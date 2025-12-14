from pydantic import BaseModel

from typing import Optional, List

class AppSettings(BaseModel):
    font_size: int = 12
    indent_size: int = 2
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

