from typing import List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.api.deps import RoleChecker, get_current_user
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketSummaryResponse
from app.services.ticket_service import TicketService
from app.services.location_service import LocationService, calculate_haversine_distance
from app.services.asset_service import AssetService
from app.core import constants

router = APIRouter()


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tickets"],
)
async def create_ticket(
    ticket_in: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new work ticket for an asset."""
    # Enforce that the asset is nearby the technician
    asset_service = AssetService(db)
    asset = await asset_service.get_asset(ticket_in.asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    loc_service = LocationService(db)
    user_location = await loc_service.get_latest_location(current_user.id)
    if not user_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your location is unknown. Please verify location settings to create tickets."
        )

    distance = calculate_haversine_distance(
        user_location.latitude,
        user_location.longitude,
        asset.latitude,
        asset.longitude
    )
    if distance > 500.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset '{asset.name}' is too far ({distance:.1f}m away). You can only create tickets for assets within 500m."
        )

    service = TicketService(db)
    return await service.create_ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        technician_id=current_user.id,
        asset_id=ticket_in.asset_id,
        priority=ticket_in.priority,
    )


@router.get(
    "",
    response_model=List[TicketResponse],
    status_code=status.HTTP_200_OK,
    tags=["Tickets"],
)
async def list_tickets(
    skip: int = 0,
    limit: int = 100,
    my_tickets_only: bool = Query(False, description="Filter only to tickets assigned to me"),
    latitude: float | None = Query(None, ge=-90.0, le=90.0),
    longitude: float | None = Query(None, ge=-180.0, le=180.0),
    radius_meters: float = Query(500.0, ge=1.0, le=50000.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List system tickets with optional technician assignment filter."""
    service = TicketService(db)
    
    lat = latitude
    lon = longitude
    
    if lat is None or lon is None:
        loc_service = LocationService(db)
        latest_loc = await loc_service.get_latest_location(current_user.id)
        if latest_loc:
            lat = latest_loc.latitude
            lon = latest_loc.longitude
            
    if lat is not None and lon is not None:
        # Find nearby tickets
        tickets = await service.find_nearby_tickets(lat, lon, radius_meters)
        if my_tickets_only:
            tickets = [t for t in tickets if t.technician_id == current_user.id]
        return tickets

    # If no location is available, do not return any tickets (or return empty list)
    return []


@router.get(
    "/nearby",
    response_model=List[TicketResponse],
    status_code=status.HTTP_200_OK,
    tags=["Tickets"],
)
async def find_nearby_tickets(
    latitude: float = Query(..., ge=-90.0, le=90.0, examples=[37.7749]),
    longitude: float = Query(..., ge=-180.0, le=180.0, examples=[-122.4194]),
    radius_meters: float = Query(50.0, ge=1.0, le=5000.0, examples=[50.0]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Locate open tickets near specified coordinates."""
    service = TicketService(db)
    return await service.find_nearby_tickets(latitude, longitude, radius_meters)


@router.get(
    "/{id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    tags=["Tickets"],
)
async def get_ticket(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full details of a specific ticket."""
    service = TicketService(db)
    return await service.get_ticket(id)


@router.get(
    "/{id}/summary",
    response_model=TicketSummaryResponse,
    status_code=status.HTTP_200_OK,
    tags=["Tickets"],
)
async def get_ticket_summary(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve synthetic audio-friendly summary description of a ticket."""
    service = TicketService(db)
    summary = await service.summarize_ticket(id)
    return {"summary": summary}


@router.patch(
    "/{id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    tags=["Tickets"],
)
async def update_ticket(
    id: int,
    ticket_in: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Modify details of an active ticket."""
    service = TicketService(db)
    
    # Verify proximity of user to the ticket's asset before updating
    ticket = await service.get_ticket(id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        
    loc_service = LocationService(db)
    user_location = await loc_service.get_latest_location(current_user.id)
    if not user_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your location is unknown. Cannot update ticket."
        )
        
    distance = calculate_haversine_distance(
        user_location.latitude,
        user_location.longitude,
        ticket.asset.latitude,
        ticket.asset.longitude
    )
    if distance > 500.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset '{ticket.asset.name}' is too far ({distance:.1f}m away). You can only update tickets within 500m."
        )

    update_dict = ticket_in.model_dump(exclude_unset=True)
    if "status" in update_dict:
        new_status = update_dict["status"]
        if new_status == "complete":
            new_status = "completed"
            update_dict["status"] = "completed"
            
        if new_status not in ["open", "in_progress", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{new_status}'. Allowed statuses are: open, in_progress, completed."
            )
            
        # Restrict transition sequence: open -> in_progress -> completed
        current_status = ticket.status
        if current_status == "open" and new_status not in ["open", "in_progress"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="From 'open', you can only transition status to 'in_progress'."
            )
        elif current_status == "in_progress" and new_status not in ["in_progress", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="From 'in_progress', you can only transition status to 'completed'."
            )
        elif current_status == "completed" and new_status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed tickets cannot change status."
            )
            
    return await service.update_ticket(id, update_dict)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tickets"],
)
async def delete_ticket(
    id: int,
    current_user: User = Depends(RoleChecker([constants.ROLE_ADMIN, constants.ROLE_SUPERVISOR])),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a ticket. Requires Supervisor or Admin privileges."""
    service = TicketService(db)
    await service.repo.remove(id)
