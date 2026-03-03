from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from .config import settings

password_hasher = PasswordHash.recommended()


def get_hashed(password: str):
    return password_hasher.hash(password)


def verify_hashed(need_verifying: str, saved_hash: str):
    return password_hasher.verify(need_verifying, saved_hash)


def create_access_token(data: dict):
    data = data.copy()

    iat = datetime.now(timezone.utc)
    expire = iat + timedelta(minutes=settings.TOKEN_EXPIRY_MIN)
    data.update({"exp": expire, "iat": iat, "type": "access"})

    encoded = jwt.encode(
        data, settings.SECRET_KEY, algorithm=settings.TOKEN_ENCODE_ALGORITHM
    )
    return encoded
