"""Create tables and seed default roles/permissions + bootstrap admin."""
from __future__ import annotations

from sqlalchemy.orm import Session

from uce_api.auth import hash_password
from uce_api.config import get_settings
from uce_api.db.base import Base
from uce_api.db.models import Permission, Role, User
from uce_api.db.session import SessionLocal, engine

_DEFAULT_PERMISSIONS = [
    ("competency.read", "Read competencies and their definitions"),
    ("competency.write", "Create/update/delete competencies"),
    ("competency.execute", "Execute competencies"),
    ("competency.approve", "Approve pending executions"),
    ("memory.read", "Read memory entries"),
    ("memory.write", "Add or remove memory entries"),
    ("audit.read", "Read audit logs"),
    ("user.manage", "Manage users and roles"),
]

_DEFAULT_ROLES: dict[str, list[str]] = {
    "admin": [p[0] for p in _DEFAULT_PERMISSIONS],
    "author": [
        "competency.read",
        "competency.write",
        "competency.execute",
        "memory.read",
        "memory.write",
        "audit.read",
    ],
    "operator": [
        "competency.read",
        "competency.execute",
        "memory.read",
        "audit.read",
    ],
    "viewer": ["competency.read", "memory.read", "audit.read"],
}


def init_database() -> None:
    """Create tables, seed defaults, bootstrap admin."""
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    with SessionLocal() as db:
        _seed_permissions(db)
        _seed_roles(db)
        _bootstrap_admin(db, settings.bootstrap_admin_email, settings.bootstrap_admin_password)
        db.commit()


def _seed_permissions(db: Session) -> None:
    existing = {p.name for p in db.query(Permission).all()}
    for name, desc in _DEFAULT_PERMISSIONS:
        if name not in existing:
            db.add(Permission(name=name, description=desc))
    db.flush()


def _seed_roles(db: Session) -> None:
    perms_by_name = {p.name: p for p in db.query(Permission).all()}
    existing = {r.name: r for r in db.query(Role).all()}
    for role_name, perm_names in _DEFAULT_ROLES.items():
        role = existing.get(role_name)
        if role is None:
            role = Role(name=role_name, description=f"Default {role_name} role")
            db.add(role)
            db.flush()
        # Ensure the role has all default permissions
        role.permissions = [perms_by_name[p] for p in perm_names if p in perms_by_name]


def _bootstrap_admin(db: Session, email: str, password: str) -> None:
    if db.query(User).count() > 0:
        return
    admin_role = db.query(Role).filter_by(name="admin").first()
    user = User(
        email=email,
        full_name="Admin",
        hashed_password=hash_password(password),
        roles=[admin_role] if admin_role else [],
    )
    db.add(user)
