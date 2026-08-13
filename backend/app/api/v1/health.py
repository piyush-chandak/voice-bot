from fastapi import APIRouter, status

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """Service status health check."""
    return {"status": "healthy", "service": "Voice Technician Assistant Backend"}
