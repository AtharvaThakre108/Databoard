from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# passlib picks bcrypt's cost factor and salt automatically. bcrypt is
# deliberately slow -- exactly what you want for password hashing, since
# it resists brute force even if the hash leaks.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw_password: str) -> str:
    return pwd_context.hash(raw_password)


def verify_password(raw_password: str, password_hash: str) -> bool:
    return pwd_context.verify(raw_password, password_hash)


def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,       # user id -- no PII in the JWT payload
        "type": token_type,   # "access" or "refresh"
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(
        str(user_id),
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        str(user_id),
        timedelta(days=settings.refresh_token_expire_days),
        "refresh",
    )


class TokenError(Exception):
    """Raised for any invalid/expired/wrong-type token. dependencies.py
    turns this into a 401."""


def decode_token(token: str, expected_type: str) -> int:
    """Decode a JWT and return the user id embedded in it.

    The `expected_type` check stops a refresh token from being used
    directly as an access-token credential -- without it, anyone
    holding a 7-day refresh token could skip ever calling /auth/refresh
    and just use it on protected routes, defeating the point of having
    two token lifetimes.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired.")
    except jwt.InvalidTokenError:
        raise TokenError("Token is invalid.")

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a '{expected_type}' token.")

    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        raise TokenError("Token payload is malformed.")