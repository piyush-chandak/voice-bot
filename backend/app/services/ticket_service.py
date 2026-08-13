from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.ticket import Ticket
from app.database.repositories.ticket_repository import TicketRepository
from app.core.exceptions import NotFoundException


class TicketService:
    def __init__(self, db: AsyncSession):
        self.repo = TicketRepository(db)

    async def get_ticket(self, ticket_id: int) -> Ticket:
        ticket = await self.repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundException(f"Ticket with ID {ticket_id} not found")
        return ticket

    async def list_tickets(self, skip: int = 0, limit: int = 100) -> List[Ticket]:
        return await self.repo.get_multi(skip=skip, limit=limit)

    async def list_my_tickets(self, technician_id: int, skip: int = 0, limit: int = 100) -> List[Ticket]:
        return await self.repo.get_by_technician(technician_id, skip, limit)

    async def find_nearby_tickets(
        self, latitude: float, longitude: float, radius_meters: float = 50.0
    ) -> List[Ticket]:
        return await self.repo.find_nearby_tickets(latitude, longitude, radius_meters)

    async def create_ticket(
        self, title: str, description: str, technician_id: int, asset_id: int, priority: str = "medium"
    ) -> Ticket:
        ticket = Ticket(
            title=title,
            description=description,
            technician_id=technician_id,
            asset_id=asset_id,
            priority=priority,
            status="open",
        )
        created = await self.repo.create(ticket)
        # Fetch with preloaded relations
        return await self.get_ticket(created.id)

    async def update_ticket(self, ticket_id: int, update_data: Dict[str, Any]) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        await self.repo.update(ticket, update_data)
        # Fetch with preloaded relations
        return await self.get_ticket(ticket_id)

    async def search_tickets(
        self,
        query: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        technician_id: int | None = None,
        asset_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ticket]:
        return await self.repo.search_tickets(
            query=query,
            status=status,
            priority=priority,
            technician_id=technician_id,
            asset_id=asset_id,
            skip=skip,
            limit=limit,
        )

    async def assign_ticket(self, ticket_id: int, technician_id: int) -> Ticket:
        return await self.update_ticket(ticket_id, {"technician_id": technician_id})

    async def start_service(self, ticket_id: int) -> Ticket:
        return await self.update_ticket(ticket_id, {"status": "in_progress"})

    async def complete_service(self, ticket_id: int) -> Ticket:
        return await self.update_ticket(ticket_id, {"status": "completed"})

    async def upload_service_images(self, ticket_id: int, image_urls: List[str]) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        image_note = f"\n[Service Images Uploaded]: {', '.join(image_urls)}"
        updated_desc = (ticket.description or "") + image_note
        return await self.update_ticket(ticket_id, {"description": updated_desc})

    async def add_service_notes(self, ticket_id: int, notes: str) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        note_entry = f"\n[Technician Note]: {notes}"
        updated_desc = (ticket.description or "") + note_entry
        return await self.update_ticket(ticket_id, {"description": updated_desc})

    async def close_ticket(self, ticket_id: int) -> Ticket:
        return await self.update_ticket(ticket_id, {"status": "closed"})

    async def summarize_ticket(self, ticket_id: int) -> str:
        ticket = await self.get_ticket(ticket_id)
        asset_name = ticket.asset.name if ticket.asset else f"Asset #{ticket.asset_id}"
        return (
            f"Ticket #{ticket.id} [{ticket.priority.upper()}]: '{ticket.title}' "
            f"for asset '{asset_name}'. Status is currently '{ticket.status}'. "
            f"Details: {ticket.description}"
        )

