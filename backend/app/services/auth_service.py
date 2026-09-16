import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse, UserResponse


def build_user_response(user: User, db: Session | None = None) -> UserResponse:
    from app.services import quota_service

    effective_tier = quota_service.get_effective_user_tier(db, user) if db else user.tier
    quotas = quota_service.get_user_quotas(effective_tier)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tier=effective_tier,
        pro_expires_at=user.pro_expires_at,
        quotas=quotas,
        is_active=user.is_active,
    )


def create_user_token(user: User, db: Session | None = None) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(
            subject=str(user.id),
            role=user.role.value,
        ),
        user=build_user_response(user, db),
    )


def register_user(db: Session, data: RegisterRequest) -> TokenResponse:
    existing_user = db.execute(
        select(User).where(User.email == data.email)
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    new_user = User(
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return create_user_token(new_user, db)


def authenticate_user(db: Session, *, email: str, password: str) -> TokenResponse:
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if (
        not user
        or not user.password_hash
        or not verify_password(password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return create_user_token(user, db)


def login_with_google(db: Session, credential: str) -> TokenResponse:
    """Verify Google ID Token, then upsert user and return system JWT."""
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    try:
        id_info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {exc}",
        )

    email: str = id_info["email"]
    full_name: str = id_info.get("name", email)
    google_sub: str = id_info["sub"]

    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if user is None:
        # Provision new user
        user = User(
            email=email,
            full_name=full_name,
            google_id=google_sub,
            password_hash=None,
            role=UserRole.USER,
            is_active=True,
        )
        db.add(user)
    else:
        # User already exists — link google_id if not linked
        if user.google_id is None:
            user.google_id = google_sub

    db.commit()
    db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return create_user_token(user, db)


def get_user_from_token(db: Session, token: str) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.execute(
        select(User).where(User.id == int(user_id))
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception

    return user
