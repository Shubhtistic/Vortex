import logging
import sys
from .logging_middleware import RequestIdFilter


def setup_logging():
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | [%(request_id)s] | %(message)s"
        )
    )

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
