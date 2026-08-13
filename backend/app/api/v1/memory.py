from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.api.deps import get_current_user
from app.schemas.conversation import MemorySaveRequest, MemoryResponse
from app.services.memory_service import MemoryService

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    tags=["Memory"],
)
async def save_memory(
    mem_in: MemorySaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Store raw technical context into semantic memory."""
    service = MemoryService(db)
    await service.save_semantic_memory(current_user.id, mem_in.content)
    return {"message": "Memory saved successfully"}


@router.get(
    "",
    response_model=MemoryResponse,
    status_code=status.HTTP_200_OK,
    tags=["Memory"],
)
async def retrieve_memory(
    query: str = Query(..., min_length=1, examples=["electrical system config"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve semantically matching history or details from memory."""
    service = MemoryService(db)
    mems = await service.search_semantic_memory(current_user.id, query)
    return {"memories": mems}
