from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_token, TokenError
from app.db.database import get_db
from app.db.models import User

# HTTPBearer (not OAuth2PasswordBearer) because /auth/login takes JSON,
# not OAuth2's form-encoded flow. This just extracts
# "Authorization: Bearer <token>" for decode_token() to use.
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    # Only ever accepts ACCESS tokens -- a refresh token here gets
    # rejected by decode_token()'s type check.
    try:
        user_id = decode_token(credentials.credentials, expected_type="access")
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


def get_refresh_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    # For /auth/refresh specifically: requires a REFRESH token, doesn't
    # need to hit the DB -- we only need the id to mint a new access token.
    try:
        return decode_token(credentials.credentials, expected_type="refresh")
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )