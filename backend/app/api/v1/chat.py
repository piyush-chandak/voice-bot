from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.api.deps import get_current_user
from app.schemas.conversation import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()

@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["Conversation"],
)
async def chat_interaction(
    chat_in: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Submit a conversational statement or command to the assistant engine."""
    service = ChatService()
    result = await service.process_chat(
        session_id=chat_in.session_id,
        user_id=current_user.id,
        user_role=current_user.role,
        user_message=chat_in.message,
        latitude=chat_in.latitude,
        longitude=chat_in.longitude,
        selected_asset_id=chat_in.selected_asset_id,
    )
    return result
