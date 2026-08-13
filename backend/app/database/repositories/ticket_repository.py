from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.models.ticket import Ticket
from app.database.models.asset import Asset
from app.database.repositories.base_repository import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, db: AsyncSession):
        super().__init__(Ticket, db)

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Ticket]:
        result = await self.db.execute(
            select(Ticket)
            .options(selectinload(Ticket.asset), selectinload(Ticket.technician))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_technician(self, technician_id: int, skip: int = 0, limit: int = 100) -> List[Ticket]:
        result = await self.db.execute(
            select(Ticket)
            .filter(Ticket.technician_id == technician_id)
            .options(selectinload(Ticket.asset), selectinload(Ticket.technician))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, ticket_id: int) -> Ticket | None:
        result = await self.db.execute(
            select(Ticket)
            .filter(Ticket.id == ticket_id)
            .options(selectinload(Ticket.asset), selectinload(Ticket.technician))
        )
        return result.scalar_one_or_none()

    async def find_nearby_tickets(
        self, latitude: float, longitude: float, radius_meters: float = 50.0
    ) -> List[Ticket]:
        # Approximate distance using simple box bound filtering first
        # 1 degree lat is approx 111,000 meters. 1 degree lon is approx 111,000 * cos(lat) meters.
        # Radius 50m = ~0.00045 degrees
        delta = radius_meters / 111000.0
        result = await self.db.execute(
            select(Ticket)
            .join(Asset)
            .filter(
                Asset.latitude.between(latitude - delta, latitude + delta),
                Asset.longitude.between(longitude - delta, longitude + delta),
            )
            .options(selectinload(Ticket.asset))
        )
        tickets = list(result.scalars().all())
        return tickets

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
        stmt = select(Ticket).options(selectinload(Ticket.asset), selectinload(Ticket.technician))
        if query:
            pattern = f"%{query}%"
            stmt = stmt.filter(Ticket.title.ilike(pattern) | Ticket.description.ilike(pattern))
        if status:
            stmt = stmt.filter(Ticket.status == status)
        if priority:
            stmt = stmt.filter(Ticket.priority == priority)
        if technician_id:
            stmt = stmt.filter(Ticket.technician_id == technician_id)
        if asset_id:
            stmt = stmt.filter(Ticket.asset_id == asset_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

