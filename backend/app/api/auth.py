from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_refresh_user_id
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenPair, AccessTokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        )

    user = User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_tokens(user)


@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.lower()
    user = db.query(User).filter(User.email == email).first()

    # Deliberately vague error: don't reveal whether the email exists
    # or the password was wrong -- that's a user-enumeration leak.
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return _issue_tokens(user)


@router.post("/refresh", response_model=AccessTokenOut)
def refresh(user_id: int = Depends(get_refresh_user_id)):
    # See core/security.py for the refresh-strategy write-up. Short
    # version: frontend calls this with the refresh token whenever an
    # access token expires, to get a new 15-minute access token without
    # forcing a full login.
    return AccessTokenOut(access_token=create_access_token(user_id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user