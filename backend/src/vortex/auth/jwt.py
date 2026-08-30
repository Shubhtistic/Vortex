import time
from uuid import uuid7
import jwt as pyjwt

from .exceptions import ExpiredSignatureError, InvalidTokenError, UnexpectedJwtError
from src.vortex.shared.config import get_settings

# TTL / algorithm are set via env variables in settings


def _normalize_pem(raw: str) -> str:
    """Support both \n literal and real newlines from .env"""
    key = raw.strip().strip("'").strip('"')
    # if file contains literal \n
    if "\\n" in key:
        key = key.replace("\\n", "\n")
    return key


settings = get_settings()
private_key = _normalize_pem(settings.jwt.private_key.get_secret_value())
public_key = _normalize_pem(settings.jwt.public_key)


def create_access_token(user_id: str, org_id: str, role: str) -> str:
    """Create an access token carrying flat claims: user_id, org_id, role."""

    jti = str(uuid7())
    expiry = int(time.time()) + settings.jwt.access_token_expire_seconds

    payload = {
        "user_id": str(user_id),
        "org_id": str(org_id),
        "role": role,
        "exp": expiry,
        "jti": jti,
    }

    access_token = pyjwt.encode(
        payload,
        private_key,
        algorithm=settings.jwt.algorithm,
    )
    return access_token


def decode_and_verify_token(token: str) -> dict:
    """Decode and verify a JWT. Raises on invalid/expired/malformed tokens."""
    try:
        return pyjwt.decode(
            token,
            public_key,
            algorithms=[settings.jwt.algorithm],
        )
    except pyjwt.ExpiredSignatureError:
        raise ExpiredSignatureError
    except pyjwt.InvalidTokenError:
        raise InvalidTokenError
    except pyjwt.PyJWTError:
        raise UnexpectedJwtError
