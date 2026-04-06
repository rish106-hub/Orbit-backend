from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, SignUpRequest
from app.schemas.user import MeResponse
from app.services.auth_service import create_session, hash_password, revoke_session, verify_password
from app.services.database_service import check_database, classify_database_error

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_me_response(user: User) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        default_timezone=user.default_timezone,
        mode="local_auth",
        calendar_provider=settings.calendar_provider,
    )


@router.get("/status")
def auth_status(db: Session = Depends(get_db)) -> dict[str, object]:
    return {
        "auth_mode": "local",
        "calendar_provider": settings.calendar_provider,
        "database_ready": check_database(db),
    }


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignUpRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        existing = db.scalar(select(User).where(User.email == payload.email))
        if existing is not None:
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(
            email=payload.email,
            display_name=payload.display_name,
            default_timezone=payload.default_timezone,
            password_hash=hash_password(payload.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token, _ = create_session(db, user)
        return AuthResponse(token=token, user=_to_me_response(user))
    except HTTPException:
        db.rollback()
        raise
    except Exception as error:
        db.rollback()
        status_code, message = classify_database_error(error)
        raise HTTPException(status_code=status_code, detail=message) from error


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user = db.scalar(select(User).where(User.email == payload.email))
        if user is None or user.password_hash is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token, _ = create_session(db, user)
        return AuthResponse(token=token, user=_to_me_response(user))
    except HTTPException:
        db.rollback()
        raise
    except Exception as error:
        db.rollback()
        status_code, message = classify_database_error(error)
        raise HTTPException(status_code=status_code, detail=message) from error


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    if authorization and authorization.startswith("Bearer "):
        revoke_session(db, authorization.removeprefix("Bearer ").strip())
    return {"success": True}
