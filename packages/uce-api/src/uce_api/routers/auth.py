from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from uce_api.auth import (
    actor_dict,
    create_access_token,
    get_current_user,
    hash_password,
    user_roles_list,
    verify_password,
)
from uce_api.db.models import Role, User
from uce_api.db.session import get_session
from uce_api.schemas import RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_session)) -> UserOut:
    if db.query(User).filter_by(email=body.email).first():
        raise HTTPException(status_code=400, detail="email already registered")
    operator_role = db.query(Role).filter_by(name="operator").first()
    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        roles=[operator_role] if operator_role else [],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=user_roles_list(user),
    )


@router.post("/login", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session),
) -> TokenOut:
    user = db.query(User).filter_by(email=form.username).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="invalid email or password")
    token = create_access_token(subject=user.id, extra={"roles": user_roles_list(user)})
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=user_roles_list(user),
    )
