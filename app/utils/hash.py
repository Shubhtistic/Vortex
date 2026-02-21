import hashlib
import secrets


def hash_api_key(api_key: str) -> str:
    """we hash the incoming the api key and return its hashed version"""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def generate_api_key(prefix: str = "vtx_pub") -> tuple[str, str]:
    """
    Generates a secure api key and its hash
    returns -> (raw_api_key, hashed_api_key)
    """
    # generate a random long string
    random_part = secrets.token_urlsafe(32)
    raw_api_key = f"{prefix}_{random_part}"

    # hash it
    hashed_key = hash_api_key(raw_api_key)

    return raw_api_key, hashed_key
