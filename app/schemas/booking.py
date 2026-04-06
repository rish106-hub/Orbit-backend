from datetime import datetime, time
import uuid

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class BookingPageUpdate(BaseModel):
    slug: str = Field(min_length=3)
    title: str = Field(min_length=1)
    active: bool = True
    default_duration_minutes: int = Field(ge=15, le=180)
    working_days: list[int]
    day_start_local: time
    day_end_local: time
    buffer_before_minutes: int = Field(ge=0, le=120)
    buffer_after_minutes: int = Field(ge=0, le=120)
    minimum_notice_minutes: int = Field(ge=0, le=10080)


class BookingPageOut(APIModel, BookingPageUpdate):
    id: uuid.UUID
    user_id: uuid.UUID


class PublicBookingPageOut(BaseModel):
    slug: str
    title: str
    duration_minutes: int
    timezone: str
    active: bool
    host_name: str


class AvailabilitySlot(BaseModel):
    start: datetime
    end: datetime


class AvailabilityResponse(BaseModel):
    timezone: str
    slots: list[AvailabilitySlot]


class BookingCreateRequest(BaseModel):
    visitor_name: str = Field(min_length=1)
    visitor_email: str = Field(min_length=3)
    visitor_timezone: str
    start: datetime
    end: datetime


class BookingCreateResponse(BaseModel):
    success: bool
    booking_id: str
    host_event_id: str
