"""JWT + password hashing + auth dependencies."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from uce_api.config import get_settings
from uce_api.db.models import User
from uce_api.db.session import get_session

_bearer = OAuth2PasswordBearer(tokenUrl="/auth/login")

# bcrypt truncates at 72 bytes — encode + truncate explicitly so longer passwords
# don't blow up. (We hash a truncated form; this matches typical practice.)
def _to_bcrypt_bytes(plain: str) -> bytes:
    return plain.encode("utf-8")[:72]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_to_bcrypt_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(*, subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire, **(extra or {})}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid token: {e}") from e


def get_current_user(
    token: str = Depends(_bearer),
    db: Session = Depends(get_session),
) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="malformed token")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="user not found or inactive")
    return user


def require_permissions(*needed: str):
    """Dependency factory: require the current user to have every given permission."""

    def _dep(user: User = Depends(get_current_user)) -> User:
        granted = {p.name for role in user.roles for p in role.permissions}
        missing = [n for n in needed if n not in granted]
        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"missing permissions: {', '.join(missing)}",
            )
        return user

    return _dep


def user_roles_list(user: User) -> list[str]:
    return [r.name for r in user.roles]


def actor_dict(user: User) -> dict[str, Any]:
    return {"id": user.id, "email": user.email, "roles": user_roles_list(user)}
