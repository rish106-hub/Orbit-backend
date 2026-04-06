from __future__ import annotations

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_timezone: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    google_account = relationship("GoogleAccount", back_populates="user", uselist=False)
    calendars = relationship("Calendar", back_populates="user")
    synced_events = relationship("SyncedEvent", back_populates="user")
    booking_pages = relationship("BookingPage", back_populates="user")
    bookings = relationship("Booking", back_populates="user")
    agent_runs = relationship("AgentRun", back_populates="user")
    auth_sessions = relationship("AuthSession", back_populates="user")
