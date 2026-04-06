from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session


def check_database(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def classify_database_error(error: Exception) -> tuple[int, str]:
    if isinstance(error, IntegrityError):
        return 409, "This account already exists."
    if isinstance(error, OperationalError):
        return 503, "Orbit could not reach the database. Please retry in a moment."
    if isinstance(error, SQLAlchemyError):
        return 503, "Orbit could not save your account right now. Please retry."
    return 500, "Orbit hit an unexpected server error."
