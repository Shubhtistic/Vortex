class InvalidCredentialsError(Exception):
    """raise when org_slug/email/password combination is wrong during login — kept generic on purpose (see router)"""

    def __init__(self, email: str):
        self.email = email


# --- jwt errrors ---


class InvalidTokenError(Exception):
    """raise when a token creation fails due to token being invalid or it being expired"""


class UnexpectedJwtError(Exception):
    """catch all error for jwt"""


class ExpiredSignatureError(Exception):
    """expired jwt signature"""


# --- refresh tokn errors ---


class RefreshTokenNotFoundError(Exception):
    """raise when a refresh token is not found"""


class RefreshTokenRevokedError(Exception):
    """raise when a token is revoked"""


class SessionWindowExceededError(Exception):
    """When session window expired"""


class RefreshTokenExpiredError(Exception):
    """when the token is expired"""
