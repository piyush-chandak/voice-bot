from typing import Any, Dict, List, Optional
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.memory import Memory
from app.database.models.conversation import Conversation, Message, ConversationSummary
from app.database.repositories.conversation_repository import ConversationRepository
from app.integrations.redis import redis_client
from app.core.config import settings
from app.core.logging import logger


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversation_repo = ConversationRepository(db)

    # 1. Short Term Memory (Redis Session Cache)
    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        return await redis_client.get_json(f"session:{session_id}")

    async def save_session_state(self, session_id: str, state: Dict[str, Any]) -> None:
        await redis_client.set_json(f"session:{session_id}", state, ex=3600)

    # 2. Long Term Memory (PostgreSQL Chat History)
    async def get_or_create_conversation(self, session_id: str, user_id: int) -> Conversation:
        conv = await self.conversation_repo.get_by_session_id(session_id)
        if not conv:
            conv = Conversation(session_id=session_id, user_id=user_id)
            conv.messages = []
            conv.summaries = []
            self.db.add(conv)
            await self.db.flush()
        return conv

    async def append_message(
        self, session_id: str, user_id: int, role: str, content: str, audio_url: Optional[str] = None
    ) -> Message:
        conv = await self.get_or_create_conversation(session_id, user_id)
        msg = await self.conversation_repo.add_message(conv.id, role, content, audio_url)
        conv.messages.append(msg)
        
        # Check if conversation history is large enough to trigger automatic summarization
        messages = conv.messages
        if len(messages) >= 10 and len(messages) % 10 == 0:
            await self.trigger_summarization(conv)
        return msg

    async def trigger_summarization(self, conv: Conversation) -> str:
        # Concatenate latest messages
        text_to_summarize = "\n".join([f"{m.role}: {m.content}" for m in conv.messages[-10:]])
        summary = f"Summary of conversation: The technician reported issues regarding assets. {text_to_summarize[:100]}..."
        await self.conversation_repo.add_summary(conv.id, summary)
        logger.info("Automatic conversation summary completed", extra={"conversation_id": conv.id})
        return summary

    async def get_conversation_history(self, session_id: str, user_id: int) -> List[Dict[str, str]]:
        conv = await self.get_or_create_conversation(session_id, user_id)
        # Sort messages by id
        sorted_messages = sorted(conv.messages, key=lambda x: x.id)
        return [{"role": m.role, "content": m.content} for m in sorted_messages]

    # 3. Semantic Memory (Vector Search)
    async def save_semantic_memory(self, user_id: int, content: str) -> Memory:
        # Mock embedding dimension 1536
        embedding = [float(x) for x in np.random.randn(1536)]
        
        memory_item = Memory(
            user_id=user_id,
            content=content,
            embedding=embedding
        )
        self.db.add(memory_item)
        await self.db.flush()
        logger.info("Saved semantic memory", extra={"user_id": user_id, "content": content})
        return memory_item

    async def search_semantic_memory(self, user_id: int, query: str, limit: int = 5) -> List[str]:
        # Perform retrieval. Since pgvector might not be loaded in standard SQLite/Postgres configurations,
        # we'll fetch all memories for the user and return contents, or simulate semantic search.
        result = await self.db.execute(
            select(Memory).filter(Memory.user_id == user_id).limit(limit)
        )
        memories = result.scalars().all()
        return [m.content for m in memories]
