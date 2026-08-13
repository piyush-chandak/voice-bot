from pydantic import BaseModel, Field


class LocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, examples=[37.7749])
    longitude: float = Field(..., ge=-180.0, le=180.0, examples=[-122.4194])
    accuracy: float | None = Field(None, examples=[15.5])


class LocationResponse(BaseModel):
    id: int = Field(..., examples=[1])
    user_id: int = Field(..., examples=[1])
    latitude: float = Field(..., examples=[37.7749])
    longitude: float = Field(..., examples=[-122.4194])
    accuracy: float | None = Field(None, examples=[15.5])

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "latitude": 37.7749,
                "longitude": -122.4194,
                "accuracy": 15.5
            }
        }
