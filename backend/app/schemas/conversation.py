from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., examples=["Hi, identify my location and assets"])
    session_id: str = Field(..., examples=["session-uuid-1234"])
    latitude: Optional[float] = Field(None, examples=[37.7749])
    longitude: Optional[float] = Field(None, examples=[-122.4194])
    selected_asset_id: Optional[int] = Field(None, examples=[1])


class ChatResponse(BaseModel):
    response: str = Field(..., examples=["Hi! I found 2 assets near you. Which one are you working on?"])
    session_id: str = Field(..., examples=["session-uuid-1234"])
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    selected_asset_id: Optional[int] = None
    intent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Hi! I found 2 assets near you. Which one are you working on?",
                "session_id": "session-uuid-1234",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "nearby_assets": [
                    {"id": 1, "name": "Main Water Pump A"}
                ]
            }
        }


class MemorySaveRequest(BaseModel):
    content: str = Field(..., min_length=1, examples=["Technician prefers using electrical panel A"])


class MemoryResponse(BaseModel):
    memories: List[str] = Field(..., examples=[["Technician prefers using electrical panel A"]])

