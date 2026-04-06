from __future__ import annotations

from datetime import date, datetime
import re
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingPage
from app.models.user import User
from app.schemas.booking import BookingPageUpdate
from app.services import calendar_service
from app.services.scheduling_service import Slot, find_free_slots


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "orbit-user"


def _unique_default_slug(db: Session, user: User) -> str:
    base = _slugify((user.display_name or user.email.split("@", 1)[0]))
    candidate = base
    suffix = 1
    while get_booking_page_by_slug(db, candidate) is not None:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def get_or_create_booking_page(db: Session, user: User) -> BookingPage:
    statement = select(BookingPage).where(BookingPage.user_id == user.id)
    page = db.scalar(statement)
    if page is None:
        page = BookingPage(
            user_id=user.id,
            slug=_unique_default_slug(db, user),
            title="Orbit Intro Meeting",
            active=True,
            default_duration_minutes=30,
            working_days=[1, 2, 3, 4, 5],
            day_start_local=datetime.strptime("09:00", "%H:%M").time(),
            day_end_local=datetime.strptime("18:00", "%H:%M").time(),
            buffer_before_minutes=0,
            buffer_after_minutes=0,
            minimum_notice_minutes=60,
        )
        db.add(page)
        db.commit()
        db.refresh(page)
    return page


def get_booking_page_by_slug(db: Session, slug: str) -> BookingPage | None:
    statement = select(BookingPage).where(BookingPage.slug == slug)
    return db.scalar(statement)


def update_booking_page(db: Session, page: BookingPage, payload: BookingPageUpdate) -> BookingPage:
    for field, value in payload.model_dump().items():
        setattr(page, field, value)
    db.commit()
    db.refresh(page)
    return page


def compute_availability(
    db: Session,
    user: User,
    page: BookingPage,
    *,
    target_date: date,
    duration_minutes: int,
    visitor_timezone: str,
) -> list[Slot]:
    host_tz = ZoneInfo(user.default_timezone)
    start = datetime.combine(target_date, page.day_start_local, tzinfo=host_tz)
    end = datetime.combine(target_date, page.day_end_local, tzinfo=host_tz)
    events = calendar_service.list_events(db, user, start, end)
    return find_free_slots(
        events=events,
        range_start=start,
        range_end=end,
        duration_minutes=duration_minutes,
        timezone_name=visitor_timezone,
        working_days=page.working_days,
        day_start_local=page.day_start_local,
        day_end_local=page.day_end_local,
        minimum_notice_minutes=page.minimum_notice_minutes,
        buffer_before_minutes=page.buffer_before_minutes,
        buffer_after_minutes=page.buffer_after_minutes,
    )


def create_booking(
    db: Session,
    user: User,
    page: BookingPage,
    *,
    visitor_name: str,
    visitor_email: str,
    visitor_timezone: str,
    start: datetime,
    end: datetime,
) -> Booking:
    overlapping = calendar_service.list_events(db, user, start, end)
    if overlapping:
        raise ValueError("Selected slot is no longer available.")

    event = calendar_service.create_event(
        db,
        user,
        title=f"{page.title} · {visitor_name}",
        start=start,
        end=end,
        description=f"Booked by {visitor_name} <{visitor_email}>",
    )
    booking = Booking(
        booking_page_id=page.id,
        user_id=user.id,
        visitor_name=visitor_name,
        visitor_email=visitor_email,
        visitor_timezone=visitor_timezone,
        starts_at=start,
        ends_at=end,
        google_event_id=event.google_event_id,
        status="confirmed",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
