from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

pass_context = PasswordHasher()  # defaults to argon2id — current recommended variant


def hash_password(password: str) -> str:
    # hashes the password
    return pass_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        pass_context.verify(hashed_password, password)
        return True
    except VerifyMismatchError:
        return False
