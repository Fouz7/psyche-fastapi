from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest
from typing import Tuple, cast


def register_user(db: Session, payload: RegisterRequest) -> User:
    email_norm = str(payload.email).strip().lower()

    existing = (
        db.query(User)
        .filter(
            or_(
                User.username == payload.username,
                func.lower(User.email) == email_norm,
            )
        )
        .first()
    )
    if existing:
        raise ValueError("Username or email already registered")

    user = User(
        username=payload.username,
        email=email_norm,
        passwordHash=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_user(db: Session, payload: LoginRequest) -> Tuple[str, User]:
    identifier = payload.username.strip()
    email_norm = identifier.lower()

    user = (
        db.query(User)
        .filter(
            or_(
                User.username == identifier,
                func.lower(User.email) == email_norm,
            )
        )
        .first()
    )

    if not user:
        raise LookupError("User Not Found")
    if not verify_password(payload.password, user.passwordHash):
        raise PermissionError("Password Incorrect")

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return token, cast(User, user)
