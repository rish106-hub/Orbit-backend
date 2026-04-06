from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.calendar import CalendarEventsResponse, CalendarSyncRequest, CalendarSyncResponse
from app.schemas.common import EventOut
from app.services import calendar_service

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", response_model=CalendarEventsResponse)
def get_events(
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CalendarEventsResponse:
    events = calendar_service.list_events(db, user, start, end)
    return CalendarEventsResponse(events=[EventOut.model_validate(event) for event in events])


@router.post("/sync", response_model=CalendarSyncResponse)
def sync_calendar(
    payload: CalendarSyncRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CalendarSyncResponse:
    synced_count = calendar_service.seed_sample_events(db, user, payload.start, payload.end)
    return CalendarSyncResponse(synced_count=synced_count, source="local-dev")
