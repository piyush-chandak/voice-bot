from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.api.deps import get_current_user
from app.schemas.location import LocationRequest, LocationResponse
from app.services.location_service import LocationService
from app.core.exceptions import NotFoundException

router = APIRouter()


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Location"],
)
async def update_location(
    loc_in: LocationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save technician's current location details."""
    service = LocationService(db)
    location = await service.log_location(
        user_id=current_user.id,
        latitude=loc_in.latitude,
        longitude=loc_in.longitude,
        accuracy=loc_in.accuracy,
    )
    return location


@router.get(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Location"],
)
async def get_latest_location(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get technician's latest logged location."""
    service = LocationService(db)
    location = await service.get_latest_location(current_user.id)
    if not location:
        raise NotFoundException("No location history available for this user.")
    return location
