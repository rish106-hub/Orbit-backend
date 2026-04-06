from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import EventOut


class CalendarEventsResponse(BaseModel):
    events: list[EventOut]


class CalendarSyncRequest(BaseModel):
    start: datetime
    end: datetime


class CalendarSyncResponse(BaseModel):
    synced_count: int
    source: str


class CreateEventRequest(BaseModel):
    title: str = Field(min_length=1)
    start: datetime
    end: datetime
    description: str | None = None
    location: str | None = None


class MoveEventRequest(BaseModel):
    event_id: str
    new_start: datetime
    new_end: datetime
