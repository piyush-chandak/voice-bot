from pydantic import BaseModel, Field
from app.schemas.asset import AssetResponse


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, examples=["Leak in Water Valve"])
    description: str = Field(..., min_length=5, max_length=2000, examples=["Technician identified a pipe leak near the main connection."])
    asset_id: int = Field(..., examples=[1])
    priority: str = Field("medium", examples=["low", "medium", "high", "critical"])


class TicketUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200, examples=["Repaired Leak in Water Valve"])
    description: str | None = Field(None, min_length=5, max_length=2000)
    status: str | None = Field(None, examples=["open", "in_progress", "resolved", "closed"])
    priority: str | None = Field(None, examples=["low", "medium", "high", "critical"])


class TicketResponse(BaseModel):
    id: int = Field(..., examples=[1])
    title: str = Field(..., examples=["Leak in Water Valve"])
    description: str = Field(..., examples=["Technician identified a pipe leak near the main connection."])
    status: str = Field(..., examples=["open"])
    priority: str = Field(..., examples=["medium"])
    technician_id: int = Field(..., examples=[1])
    asset_id: int = Field(..., examples=[1])
    asset: AssetResponse | None = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Leak in Water Valve",
                "description": "Technician identified a pipe leak near the main connection.",
                "status": "open",
                "priority": "medium",
                "technician_id": 1,
                "asset_id": 1
            }
        }
class TicketSummaryResponse(BaseModel):
    summary: str = Field(..., examples=["Ticket #1 [MEDIUM]: Leak in Water Valve ..."])
