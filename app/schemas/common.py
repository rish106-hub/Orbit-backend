from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EventOut(APIModel):
    id: uuid.UUID
    google_event_id: str
    title: str | None
    description: str | None
    status: str
    starts_at: datetime
    ends_at: datetime
    all_day: bool
    location: str | None
    meeting_url: str | None
