from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.models.calendar import SyncedEvent


@dataclass
class Slot:
    start: datetime
    end: datetime
    score: float


def _clip_busy_events(events: list[SyncedEvent], day_start: datetime, day_end: datetime) -> list[tuple[datetime, datetime]]:
    clipped: list[tuple[datetime, datetime]] = []
    for event in events:
        start = max(event.starts_at, day_start)
        end = min(event.ends_at, day_end)
        if start < end:
            clipped.append((start, end))
    return sorted(clipped, key=lambda item: item[0])


def _subtract_busy_windows(
    day_start: datetime,
    day_end: datetime,
    busy: list[tuple[datetime, datetime]],
    duration: timedelta,
) -> list[tuple[datetime, datetime]]:
    cursor = day_start
    slots: list[tuple[datetime, datetime]] = []

    for start, end in busy:
        if cursor + duration <= start:
            slots.append((cursor, start))
        cursor = max(cursor, end)

    if cursor + duration <= day_end:
        slots.append((cursor, day_end))

    return slots


def _score_slot(slot_start: datetime, slot_end: datetime, duration: timedelta) -> float:
    available_minutes = (slot_end - slot_start).total_seconds() / 60
    duration_minutes = duration.total_seconds() / 60
    margin = max(0.0, available_minutes - duration_minutes)
    return round(min(0.99, 0.6 + margin / 300), 2)


def find_free_slots(
    *,
    events: list[SyncedEvent],
    range_start: datetime,
    range_end: datetime,
    duration_minutes: int,
    timezone_name: str,
    working_days: list[int] | None = None,
    day_start_local: time | None = None,
    day_end_local: time | None = None,
    minimum_notice_minutes: int = 0,
    buffer_before_minutes: int = 0,
    buffer_after_minutes: int = 0,
) -> list[Slot]:
    tz = ZoneInfo(timezone_name)
    duration = timedelta(minutes=duration_minutes)
    minimum_start = datetime.now(tz) + timedelta(minutes=minimum_notice_minutes)
    day_start_local = day_start_local or time(hour=9, minute=0)
    day_end_local = day_end_local or time(hour=18, minute=0)
    working_days = working_days or [1, 2, 3, 4, 5]

    current_day = range_start.astimezone(tz).date()
    last_day = range_end.astimezone(tz).date()
    slots: list[Slot] = []

    while current_day <= last_day:
        if current_day.isoweekday() not in working_days:
            current_day += timedelta(days=1)
            continue

        local_start = datetime.combine(current_day, day_start_local, tzinfo=tz)
        local_end = datetime.combine(current_day, day_end_local, tzinfo=tz)

        day_start = max(local_start, range_start.astimezone(tz))
        day_end = min(local_end, range_end.astimezone(tz))

        if day_start >= day_end:
            current_day += timedelta(days=1)
            continue

        buffered_busy = []
        for event in events:
            buffered_busy.append(
                (
                    event.starts_at - timedelta(minutes=buffer_before_minutes),
                    event.ends_at + timedelta(minutes=buffer_after_minutes),
                )
            )

        busy = sorted(
            [
                (max(start, day_start), min(end, day_end))
                for start, end in buffered_busy
                if max(start, day_start) < min(end, day_end)
            ],
            key=lambda item: item[0],
        )
        available_windows = _subtract_busy_windows(day_start, day_end, busy, duration)

        for start, end in available_windows:
            candidate_start = max(start, minimum_start)
            if candidate_start + duration <= end:
                candidate_end = candidate_start + duration
                slots.append(
                    Slot(
                        start=candidate_start,
                        end=candidate_end,
                        score=_score_slot(start, end, duration),
                    )
                )

        current_day += timedelta(days=1)

    return sorted(slots, key=lambda slot: (slot.start, -slot.score))
