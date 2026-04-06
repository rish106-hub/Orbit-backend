from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.calendar import Calendar, SyncedEvent
from app.models.user import User


class CalendarProvider(Protocol):
    provider_name: str

    def sync_range(self, db: Session, user: User, start: datetime, end: datetime) -> int: ...

    def list_events(self, db: Session, user: User, start: datetime, end: datetime) -> list[SyncedEvent]: ...

    def create_event(
        self,
        db: Session,
        user: User,
        *,
        title: str,
        start: datetime,
        end: datetime,
        description: str | None = None,
        location: str | None = None,
    ) -> SyncedEvent: ...

    def move_event(
        self,
        db: Session,
        user: User,
        *,
        event_id: str,
        new_start: datetime,
        new_end: datetime,
    ) -> SyncedEvent | None: ...


def ensure_default_calendar(db: Session, user: User) -> Calendar:
    statement = select(Calendar).where(
        Calendar.user_id == user.id,
        Calendar.selected_for_scheduling.is_(True),
    )
    calendar = db.scalar(statement)
    if calendar is None:
        calendar = Calendar(
            user_id=user.id,
            google_calendar_id="local-primary",
            summary="Orbit Calendar",
            primary_calendar=True,
            selected_for_scheduling=True,
            timezone=user.default_timezone,
        )
        db.add(calendar)
        db.commit()
        db.refresh(calendar)
    return calendar


class LocalCalendarProvider:
    provider_name = "local"

    def sync_range(self, db: Session, user: User, start: datetime, end: datetime) -> int:
        existing = self.list_events(db, user, start, end)
        if existing:
            return len(existing)

        samples = [
            ("Standup", start.replace(hour=10, minute=0), start.replace(hour=10, minute=30)),
            ("Client Review", start.replace(hour=13, minute=0), start.replace(hour=14, minute=0)),
            ("Ops Sync", start.replace(hour=16, minute=30), start.replace(hour=17, minute=15)),
        ]
        for title, event_start, event_end in samples:
            self.create_event(db, user, title=title, start=event_start, end=event_end)
        return len(samples)

    def list_events(self, db: Session, user: User, start: datetime, end: datetime) -> list[SyncedEvent]:
        ensure_default_calendar(db, user)
        statement = (
            select(SyncedEvent)
            .where(
                SyncedEvent.user_id == user.id,
                SyncedEvent.starts_at < end,
                SyncedEvent.ends_at > start,
            )
            .order_by(SyncedEvent.starts_at.asc())
        )
        return list(db.scalars(statement))

    def create_event(
        self,
        db: Session,
        user: User,
        *,
        title: str,
        start: datetime,
        end: datetime,
        description: str | None = None,
        location: str | None = None,
    ) -> SyncedEvent:
        calendar = ensure_default_calendar(db, user)
        event = SyncedEvent(
            user_id=user.id,
            calendar_id=calendar.id,
            google_event_id=f"local-{uuid.uuid4()}",
            title=title,
            description=description,
            status="confirmed",
            starts_at=start,
            ends_at=end,
            all_day=False,
            location=location,
            meeting_url=None,
            raw_payload={"source": "local-dev"},
            last_synced_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def move_event(
        self,
        db: Session,
        user: User,
        *,
        event_id: str,
        new_start: datetime,
        new_end: datetime,
    ) -> SyncedEvent | None:
        statement = select(SyncedEvent).where(
            SyncedEvent.user_id == user.id,
            SyncedEvent.google_event_id == event_id,
        )
        event = db.scalar(statement)
        if event is None:
            return None

        event.starts_at = new_start
        event.ends_at = new_end
        event.last_synced_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(event)
        return event


class GoogleCalendarProvider:
    provider_name = "google"

    def sync_range(self, db: Session, user: User, start: datetime, end: datetime) -> int:
        raise NotImplementedError("Google Calendar provider is not wired yet.")

    def list_events(self, db: Session, user: User, start: datetime, end: datetime) -> list[SyncedEvent]:
        raise NotImplementedError("Google Calendar provider is not wired yet.")

    def create_event(
        self,
        db: Session,
        user: User,
        *,
        title: str,
        start: datetime,
        end: datetime,
        description: str | None = None,
        location: str | None = None,
    ) -> SyncedEvent:
        raise NotImplementedError("Google Calendar provider is not wired yet.")

    def move_event(
        self,
        db: Session,
        user: User,
        *,
        event_id: str,
        new_start: datetime,
        new_end: datetime,
    ) -> SyncedEvent | None:
        raise NotImplementedError("Google Calendar provider is not wired yet.")


def get_calendar_provider() -> CalendarProvider:
    if settings.calendar_provider == "google":
        return GoogleCalendarProvider()
    return LocalCalendarProvider()
