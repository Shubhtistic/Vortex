import hashlib
import secrets


def hash_api_key(api_key: str) -> str:
    """we hash the incoming the api key and return its hashed version"""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

