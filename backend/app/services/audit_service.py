import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.database.models.audit import AuditLog


class AuditService:
    """Audit Logging Service recording immutable records of tool executions and agent actions."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def log_event(
        self,
        user_id: int,
        session_id: str,
        tool_name: str,
        args: Dict[str, Any],
        result: Dict[str, Any],
        authorization: str = "Authorized",
        action_taken: str = "TOOL_EXECUTION",
        model_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        event_id = f"audit-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        audit_data = {
            "event_id": event_id,
            "timestamp": now.isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "tool_name": tool_name,
            "tool_args": args,
            "result_summary": "success" if result.get("success") is not False else "error",
            "authorization": authorization,
            "action_taken": action_taken,
            "model_provider": model_provider,
        }

        # Log structured audit entry to logger
        logger.info(f"AUDIT_EVENT [{event_id}]: User {user_id} executed {tool_name}", extra=audit_data)

        # Record to database if session is present
        if self.db:
            try:
                db_audit = AuditLog(
                    user_id=user_id,
                    action=action_taken,
                    details=f"Tool: {tool_name} | Event: {event_id} | Status: {audit_data['result_summary']}",
                )
                self.db.add(db_audit)
                await self.db.flush()
            except Exception as e:
                logger.warning(f"Could not persist audit record to database: {e}")

        return audit_data
