from pydantic import BaseModel, Field


class AssetResponse(BaseModel):
    id: int = Field(..., examples=[1])
    name: str = Field(..., examples=["Main Water Pump A"])
    description: str | None = Field(None, examples=["Primary water distribution valve and flow rate pump."])
    sku: str = Field(..., examples=["PUMP-WTR-001"])
    latitude: float = Field(..., examples=[37.7749])
    longitude: float = Field(..., examples=[-122.4194])
    status: str = Field(..., examples=["operational"])

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Main Water Pump A",
                "description": "Primary water distribution valve and flow rate pump.",
                "sku": "PUMP-WTR-001",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "status": "operational"
            }
        }


class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Main Water Pump A"])
    description: str | None = Field(None, max_length=500, examples=["Primary water distribution valve and flow rate pump."])
    sku: str = Field(..., min_length=1, max_length=50, examples=["PUMP-WTR-001"])
    latitude: float = Field(..., ge=-90.0, le=90.0, examples=[37.7749])
    longitude: float = Field(..., ge=-180.0, le=180.0, examples=[-122.4194])
    status: str = Field("operational", min_length=1, max_length=50, examples=["operational"])


class AssetUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100, examples=["Main Water Pump A"])
    description: str | None = Field(None, max_length=500, examples=["Primary water distribution valve and flow rate pump."])
    sku: str | None = Field(None, min_length=1, max_length=50, examples=["PUMP-WTR-001"])
    latitude: float | None = Field(None, ge=-90.0, le=90.0, examples=[37.7749])
    longitude: float | None = Field(None, ge=-180.0, le=180.0, examples=[-122.4194])
    status: str | None = Field(None, min_length=1, max_length=50, examples=["operational"])

