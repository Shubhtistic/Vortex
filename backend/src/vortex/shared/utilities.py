from typing import Any


def reject_blank_text(value: Any) -> Any:
    """Reject blank or whitespace-only strings in user supplied input."""
    if value is None or not isinstance(value, str):
        return value
    if not value.strip():
        raise ValueError("must not be empty or contain only whitespace")
    return value
