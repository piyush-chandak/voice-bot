import math
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.audit import Location


class BaseLocationProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def get_current_location(self, user_id: int, context: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Retrieve current latitude/longitude for technician context."""
        pass


class DeviceGPSLocationProvider(BaseLocationProvider):
    @property
    def provider_name(self) -> str:
        return "device_gps"

    async def get_current_location(self, user_id: int, context: Dict[str, Any]) -> Optional[Dict[str, float]]:
        lat = context.get("latitude")
        lon = context.get("longitude")
        if lat is not None and lon is not None:
            return {"latitude": float(lat), "longitude": float(lon)}
        return None


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in meters between two points on the earth."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class LocationService:
    def __init__(self, db: AsyncSession, provider: Optional[BaseLocationProvider] = None):
        self.db = db
        self.provider = provider or DeviceGPSLocationProvider()

    async def get_current_location(self, user_id: int, context: Dict[str, Any]) -> Optional[Dict[str, float]]:
        loc = await self.provider.get_current_location(user_id, context)
        if loc:
            return loc
        # Fallback to database last logged location
        db_loc = await self.get_latest_location(user_id)
        if db_loc:
            return {"latitude": db_loc.latitude, "longitude": db_loc.longitude}
        return None

    async def log_location(
        self, user_id: int, latitude: float, longitude: float, accuracy: float = None
    ) -> Location:
        location = Location(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
        )
        self.db.add(location)
        await self.db.flush()
        return location

    async def get_latest_location(self, user_id: int) -> Location | None:
        result = await self.db.execute(
            select(Location)
            .filter(Location.user_id == user_id)
            .order_by(Location.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
