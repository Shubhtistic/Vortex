from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Any
from datetime import datetime, timezone
import uuid


## always use  pascalCase for classes and never use Snake case


class CreateEvent(BaseModel):
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    # we use default factor because it will call the function everytime this function is ran
    # if we use deafult it will calculate the default value once and use it over and over again

    event_type: str

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # we used lambda beacuse pydantic expects a function ref
    # so lambda runs and that referance is passed to Field class of pydantic
    # default_factory needs a function that will be called each time a model is created.
    # Not the result of a function — the function itself.
    # datetime.now(timezone.utc) -> returns value

    url: HttpUrl
    payload: Optional[dict[str, Any]] = None

    # Pydantic specifically looks for a nested class named Config to find
    # meta-settings' (settings about the settings).
    # Should be Config and not config -> Capital 'C'
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "button_click",
                "url": "https://example.com/pricing",
                "payload": {"button_color": "blue", "user_id": 123},
            }
        }
