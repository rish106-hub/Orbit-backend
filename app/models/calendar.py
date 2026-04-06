from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TextStatusMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Calendar(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "calendars"
    __table_args__ = (
        Index("ix_calendars_user_id", "user_id"),
        UniqueConstraint("user_id", "google_calendar_id", name="uq_calendars_user_google_calendar_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    google_calendar_id: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    primary_calendar: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    selected_for_scheduling: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timezone: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="calendars")
    synced_events = relationship("SyncedEvent", back_populates="calendar")


class SyncedEvent(UUIDPrimaryKeyMixin, TimestampMixin, TextStatusMixin, Base):
    __tablename__ = "synced_events"
    __table_args__ = (
        Index("ix_synced_events_user_id", "user_id"),
        Index("ix_synced_events_calendar_id", "calendar_id"),
        Index("ix_synced_events_starts_at", "starts_at"),
        UniqueConstraint("calendar_id", "google_event_id", name="uq_synced_events_calendar_google_event_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    calendar_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("calendars.id", ondelete="CASCADE"), nullable=False)
    google_event_id: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    meeting_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="synced_events")
    calendar = relationship("Calendar", back_populates="synced_events")
