class UserAlreadyExistsError(Exception):
    """raise when a user with this email already exists"""

    def __init__(self, email: str):
        self.email = email


class UserNotFoundError(Exception):
    """raise when a user lookup by id/email finds no matching row"""

    def __init__(self, identifier: str):
        self.identifier = identifier
