from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.asset import Asset
from app.database.repositories.base_repository import BaseRepository


class AssetRepository(BaseRepository[Asset]):
    def __init__(self, db: AsyncSession):
        super().__init__(Asset, db)

    async def find_nearby_assets(
        self, latitude: float, longitude: float, radius_meters: float = 50.0
    ) -> List[Asset]:
        # Approximate distance using simple box bounding
        # ~111,000 meters per degree lat/lon
        delta = radius_meters / 111000.0
        result = await self.db.execute(
            select(Asset).filter(
                Asset.latitude.between(latitude - delta, latitude + delta),
                Asset.longitude.between(longitude - delta, longitude + delta),
            )
        )
        return list(result.scalars().all())

    async def get_by_sku(self, sku: str) -> Asset | None:
        result = await self.db.execute(select(Asset).filter(Asset.sku == sku))
        return result.scalar_one_or_none()

    async def search_assets(
        self, query: str | None = None, status: str | None = None, skip: int = 0, limit: int = 100
    ) -> List[Asset]:
        stmt = select(Asset)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.filter(Asset.name.ilike(pattern) | Asset.description.ilike(pattern) | Asset.sku.ilike(pattern))
        if status:
            stmt = stmt.filter(Asset.status == status)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

