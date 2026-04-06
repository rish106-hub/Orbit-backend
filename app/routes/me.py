from fastapi import APIRouter, Depends

from app.config import settings
from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import MeResponse

router = APIRouter()


@router.get("/me", response_model=MeResponse)
def get_me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        default_timezone=user.default_timezone,
        mode="local_auth",
        calendar_provider=settings.calendar_provider,
    )
