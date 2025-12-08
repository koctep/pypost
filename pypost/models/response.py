from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ResponseData:
    status_code: int
    headers: Dict[str, str]
    body: str
    elapsed_time: float # seconds
    size: int # bytes
