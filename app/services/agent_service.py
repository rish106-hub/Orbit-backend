from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.booking import AgentRun, BookingPage
from app.models.user import User
from app.schemas.agent import AgentQueryResponse, ProposedAction
from app.services import booking_service, calendar_service
from app.services.scheduling_service import find_free_slots


def _create_run(db: Session, user: User, text: str, intent: str, status: str, result_summary: str) -> AgentRun:
    run = AgentRun(
        user_id=user.id,
        input_text=text,
        detected_intent=intent,
        status=status,
        result_summary=result_summary,
        tool_trace=None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def detect_intent(text: str) -> str:
    lower = text.lower()
    if "booking" in lower:
        return "open_booking_settings"
    if "move" in lower or "reschedule" in lower:
        return "move_event"
    if "free" in lower or "slot" in lower or "when am i free" in lower:
        return "find_free_time"
    if "create" in lower or "schedule" in lower or "block" in lower:
        return "create_event"
    return "show_schedule"


def handle_query(db: Session, user: User, text: str) -> AgentQueryResponse:
    intent = detect_intent(text)
    tz = ZoneInfo(user.default_timezone)
    now = datetime.now(tz)
    tomorrow = now + timedelta(days=1)
    range_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    range_end = range_start + timedelta(days=1)

    if intent == "show_schedule":
        events = calendar_service.list_events(db, user, range_start, range_end)
        run = _create_run(db, user, text, intent, "completed", "Returned today's schedule")
        return AgentQueryResponse(
            run_id=str(run.id),
            intent=intent,
            message=f"You have {len(events)} scheduled items today.",
            requires_confirmation=False,
            data={"events": [event.google_event_id for event in events]},
        )

    if intent == "find_free_time":
        start = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        end = tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
        events = calendar_service.list_events(db, user, start, end)
        slots = find_free_slots(
            events=events,
            range_start=start,
            range_end=end,
            duration_minutes=120,
            timezone_name=user.default_timezone,
        )
        run = _create_run(db, user, text, intent, "completed", "Returned free time suggestions")
        return AgentQueryResponse(
            run_id=str(run.id),
            intent=intent,
            message="I found free time tomorrow." if slots else "I could not find a 2 hour free block tomorrow.",
            requires_confirmation=False,
            data={
                "candidate_slots": [
                    {"start": slot.start.isoformat(), "end": slot.end.isoformat(), "score": slot.score}
                    for slot in slots[:3]
                ]
            },
        )

    if intent == "create_event":
        start = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end = tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)
        run = _create_run(db, user, text, intent, "pending_confirmation", "Prepared create event action")
        return AgentQueryResponse(
            run_id=str(run.id),
            intent=intent,
            message="I can block Deep Work tomorrow from 10:00 AM to 12:00 PM.",
            requires_confirmation=True,
            proposed_action=ProposedAction(
                tool_name="calendar_create_event",
                arguments={
                    "title": "Deep Work",
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "description": "Created by Orbit",
                },
            ),
        )

    if intent == "move_event":
        events = calendar_service.list_events(db, user, range_start, range_end + timedelta(days=7))
        if not events:
            run = _create_run(db, user, text, intent, "completed", "No event available to move")
            return AgentQueryResponse(
                run_id=str(run.id),
                intent=intent,
                message="I could not find an event to move yet.",
                requires_confirmation=False,
            )
        event = events[0]
        duration = event.ends_at - event.starts_at
        new_start = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        new_end = new_start + duration
        run = _create_run(db, user, text, intent, "pending_confirmation", "Prepared move event action")
        return AgentQueryResponse(
            run_id=str(run.id),
            intent=intent,
            message=f"I can move {event.title or 'this event'} to tomorrow at 3:00 PM.",
            requires_confirmation=True,
            proposed_action=ProposedAction(
                tool_name="calendar_move_event",
                arguments={
                    "event_id": event.google_event_id,
                    "new_start": new_start.isoformat(),
                    "new_end": new_end.isoformat(),
                },
            ),
        )

    page = booking_service.get_or_create_booking_page(db, user)
    run = _create_run(db, user, text, intent, "completed", "Returned booking settings route")
    return AgentQueryResponse(
        run_id=str(run.id),
        intent="open_booking_settings",
        message=f"Your booking page is ready at /b/{page.slug}.",
        requires_confirmation=False,
        data={"slug": page.slug},
    )
