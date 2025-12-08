from pydantic import BaseModel

class AppSettings(BaseModel):
    font_size: int = 12

