from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth_session import AuthSession
from app.models.user import User

PBKDF2_ITERATIONS = 120_000
SESSION_DAYS = 30


def hash_password(password: str, *, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    comparison = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(comparison, digest)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, user: User) -> tuple[str, AuthSession]:
    raw_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=now + timedelta(days=SESSION_DAYS),
        last_used_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return raw_token, session


def revoke_session(db: Session, token: str) -> None:
    statement = select(AuthSession).where(AuthSession.token_hash == hash_token(token))
    session = db.scalar(statement)
    if session is not None:
        db.delete(session)
        db.commit()
