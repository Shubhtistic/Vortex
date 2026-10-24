class RedpandaNotStartedError(RuntimeError):
    """Raised when a message is published before the Redpanda producer starts."""


class RedpandaPublishError(RuntimeError):
    """Raised when a Redpanda message cannot be serialized or published."""


class InvalidEventError(Exception):
    """Raised when an event cannot be fixed by retrying it."""
