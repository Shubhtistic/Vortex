import secrets

from blake3 import blake3

from src.vortex.shared.config import get_settings

# ======= UTILITY FUNCTIONS =========


def hash_api_key(raw_api_key: str) -> str:
    """hash the api key"""

    return blake3(raw_api_key.encode()).hexdigest()


def create_api_key() -> str:
    """create the api key using secrets module"""

    settings = get_settings()

    api_key_prefix: str = settings.project.api_key_prefix
    random_part = secrets.token_urlsafe(32)

    return api_key_prefix + random_part
