from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.booking import (
    AvailabilityResponse,
    AvailabilitySlot,
    BookingCreateRequest,
    BookingCreateResponse,
    BookingPageOut,
    BookingPageUpdate,
    PublicBookingPageOut,
)
from app.services import booking_service

router = APIRouter(tags=["booking"])


@router.get("/booking-page", response_model=BookingPageOut)
def get_booking_page(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingPageOut:
    page = booking_service.get_or_create_booking_page(db, user)
    return BookingPageOut.model_validate(page)


@router.put("/booking-page", response_model=BookingPageOut)
def update_booking_page(
    payload: BookingPageUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingPageOut:
    page = booking_service.get_or_create_booking_page(db, user)
    updated = booking_service.update_booking_page(db, page, payload)
    return BookingPageOut.model_validate(updated)


@router.get("/public/booking-pages/{slug}", response_model=PublicBookingPageOut)
def get_public_booking_page(slug: str, db: Session = Depends(get_db)) -> PublicBookingPageOut:
    page = booking_service.get_booking_page_by_slug(db, slug)
    if page is None:
        raise HTTPException(status_code=404, detail="Booking page not found")
    user = page.user
    return PublicBookingPageOut(
        slug=page.slug,
        title=page.title,
        duration_minutes=page.default_duration_minutes,
        timezone=user.default_timezone,
        active=page.active,
        host_name=user.display_name or "Orbit Host",
    )


@router.get("/public/booking-pages/{slug}/availability", response_model=AvailabilityResponse)
def get_public_availability(
    slug: str,
    date_value: date = Query(alias="date"),
    duration: int = Query(),
    visitor_timezone: str = Query(),
    db: Session = Depends(get_db),
) -> AvailabilityResponse:
    page = booking_service.get_booking_page_by_slug(db, slug)
    if page is None:
        raise HTTPException(status_code=404, detail="Booking page not found")
    user = page.user
    slots = booking_service.compute_availability(
        db,
        user,
        page,
        target_date=date_value,
        duration_minutes=duration,
        visitor_timezone=visitor_timezone,
    )
    return AvailabilityResponse(
        timezone=visitor_timezone,
        slots=[AvailabilitySlot(start=slot.start, end=slot.end) for slot in slots],
    )


@router.post("/public/booking-pages/{slug}/book", response_model=BookingCreateResponse)
def create_public_booking(
    slug: str,
    payload: BookingCreateRequest,
    db: Session = Depends(get_db),
) -> BookingCreateResponse:
    page = booking_service.get_booking_page_by_slug(db, slug)
    if page is None:
        raise HTTPException(status_code=404, detail="Booking page not found")
    user = page.user
    try:
        booking = booking_service.create_booking(
            db,
            user,
            page,
            visitor_name=payload.visitor_name,
            visitor_email=str(payload.visitor_email),
            visitor_timezone=payload.visitor_timezone,
            start=payload.start,
            end=payload.end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return BookingCreateResponse(
        success=True,
        booking_id=str(booking.id),
        host_event_id=booking.google_event_id or "",
    )
