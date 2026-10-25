"""OpenAPI documentation for event routes validated outside FastAPI's Pydantic path."""

import msgspec

from .schemas import EventIngestionBatch


EVENTS_OPENAPI_EXTRA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": msgspec.json.schema(EventIngestionBatch),
            }
        },
    },
    "responses": {
        "202": {
            "description": "The event batch was accepted for asynchronous processing.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "status_code": {"type": "integer", "example": 202},
                            "data": {},
                            "meta": {},
                        },
                        "required": ["message", "status_code", "data", "meta"],
                    }
                }
            },
        },
        "422": {"description": "The JSON body or one of its event records is invalid."},
    },
}
