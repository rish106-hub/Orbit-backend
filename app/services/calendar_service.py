from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.calendar import SyncedEvent
from app.models.user import User
from app.services.calendar_provider import get_calendar_provider


def list_events(db: Session, user: User, start: datetime, end: datetime) -> list[SyncedEvent]:
    return get_calendar_provider().list_events(db, user, start, end)


def create_event(
    db: Session,
    user: User,
    *,
    title: str,
    start: datetime,
    end: datetime,
    description: str | None = None,
    location: str | None = None,
) -> SyncedEvent:
    return get_calendar_provider().create_event(
        db,
        user,
        title=title,
        start=start,
        end=end,
        description=description,
        location=location,
    )


def move_event(
    db: Session,
    user: User,
    *,
    event_id: str,
    new_start: datetime,
    new_end: datetime,
) -> SyncedEvent | None:
    return get_calendar_provider().move_event(
        db,
        user,
        event_id=event_id,
        new_start=new_start,
        new_end=new_end,
    )


def seed_sample_events(db: Session, user: User, start: datetime, end: datetime) -> int:
    return get_calendar_provider().sync_range(db, user, start, end)
