import uuid

from pydantic import BaseModel


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    default_timezone: str
    mode: str
    calendar_provider: str
