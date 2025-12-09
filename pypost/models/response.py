from dataclasses import dataclass
from typing import Dict, Any
import json

@dataclass
class ResponseData:
    status_code: int
    headers: Dict[str, str]
    body: str
    elapsed_time: float # seconds
    size: int # bytes

    def json(self) -> Any:
        """Parses the body as JSON."""
        return json.loads(self.body)

    @property
    def text(self) -> str:
        """Returns the body as text (alias for body)."""
        return self.body
