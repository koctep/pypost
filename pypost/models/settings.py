from pydantic import BaseModel

from typing import Optional, List

class AppSettings(BaseModel):
    font_size: int = 12
    config_version: int = 1
    revision: int = 0
    last_environment_id: Optional[str] = None
    open_tabs: List[str] = []

