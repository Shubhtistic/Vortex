from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Any


## always use  pascalCase for classes and never use Snake_case


class CreateEvent(BaseModel):
    url: str
    event_type: str
    payload: Optional[dict[str, Any]] = {}
