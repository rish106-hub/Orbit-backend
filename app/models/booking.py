from __future__ import annotations

import uuid
from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Text, Time
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TextStatusMixin, TimestampMixin, UUIDPrimaryKeyMixin


class BookingPage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "booking_pages"
    __table_args__ = (Index("ix_booking_pages_user_id", "user_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    working_days: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    day_start_local: Mapped[time] = mapped_column(Time, nullable=False)
    day_end_local: Mapped[time] = mapped_column(Time, nullable=False)
    buffer_before_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    buffer_after_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minimum_notice_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="booking_pages")
    bookings = relationship("Booking", back_populates="booking_page")


class Booking(UUIDPrimaryKeyMixin, TimestampMixin, TextStatusMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_booking_page_id", "booking_page_id"),
        Index("ix_bookings_user_id", "user_id"),
        Index("ix_bookings_starts_at", "starts_at"),
    )

    booking_page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("booking_pages.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    visitor_name: Mapped[str] = mapped_column(Text, nullable=False)
    visitor_email: Mapped[str] = mapped_column(Text, nullable=False)
    visitor_timezone: Mapped[str] = mapped_column(Text, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    google_event_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    booking_page = relationship("BookingPage", back_populates="bookings")
    user = relationship("User", back_populates="bookings")


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, TextStatusMixin, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_user_id", "user_id"),
        Index("ix_agent_runs_created_at", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    detected_intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_trace: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="agent_runs")
