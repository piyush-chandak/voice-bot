from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.models.conversation import Conversation, Message, ConversationSummary
from app.database.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db: AsyncSession):
        super().__init__(Conversation, db)

    async def get_by_session_id(self, session_id: str) -> Optional[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .filter(Conversation.session_id == session_id)
            .options(selectinload(Conversation.messages), selectinload(Conversation.summaries))
        )
        return result.scalar_one_or_none()

    async def add_message(
        self, conversation_id: int, role: str, content: str, audio_url: Optional[str] = None
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            audio_url=audio_url,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def add_summary(self, conversation_id: int, summary_text: str) -> ConversationSummary:
        summary = ConversationSummary(
            conversation_id=conversation_id,
            summary_text=summary_text,
        )
        self.db.add(summary)
        await self.db.flush()
        return summary
