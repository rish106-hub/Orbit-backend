from collections.abc import Generator
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.auth_session import AuthSession
from app.models.user import User
from app.services.auth_service import hash_token


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")

    token = authorization.removeprefix("Bearer ").strip()
    statement = select(AuthSession).where(AuthSession.token_hash == hash_token(token))
    session = db.scalar(statement)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid auth token")

    if session.expires_at <= datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")

    session.last_used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session.user
