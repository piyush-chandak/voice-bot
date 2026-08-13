import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, WebSocket, WebSocketDisconnect, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db, async_session_maker
from app.database.models.user import User
from app.api.deps import get_current_user
from app.core import security
from app.core.logging import logger
from app.schemas.conversation import ChatResponse
from app.integrations.deepgram import get_speech_provider
from app.services.chat_service import ChatService

router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["Conversation"],
)
async def process_voice_input(
    session_id: str = Form(..., description="Active session ID"),
    latitude: Optional[float] = Form(None, description="Current latitude"),
    longitude: Optional[float] = Form(None, description="Current longitude"),
    file: UploadFile = File(..., description="Audio file containing speech input"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload audio speech recording, transcribe, and route to the conversation engine."""
    audio_data = await file.read()
    stt_service = get_speech_provider()
    
    # 1. Transcribe audio to text
    transcription = await stt_service.transcribe(audio_data)
    logger.info("Voice input transcribed", extra={"transcription": transcription, "session_id": session_id})

    # 2. Run chat processing with the transcribed text
    chat_service = ChatService(db)
    result = await chat_service.process_chat(
        session_id=session_id,
        user_id=current_user.id,
        user_role=current_user.role,
        user_message=transcription,
        latitude=latitude,
        longitude=longitude,
    )
    return result


@router.websocket("/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    """Bidirectional WebSocket for real-time speech transcription and streaming responses."""
    await websocket.accept()
    logger.info("WebSocket connection established")

    # 1. Perform authentication check from query parameters (since standard WS headers are limited)
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
        return

    payload = security.decode_access_token(token)
    if not payload or "user_id" not in payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    user_id = payload["user_id"]
    user_role = payload.get("role", "Technician")
    logger.info(f"WebSocket client authenticated: User {user_id}")

    try:
        while True:
            # Receive text payload (or audio binary packets)
            data = await websocket.receive_json()
            session_id = data.get("session_id")
            message = data.get("message")
            latitude = data.get("latitude")
            longitude = data.get("longitude")

            if not session_id or not message:
                await websocket.send_json({"error": "session_id and message are required"})
                continue

            async with async_session_maker() as db:
                chat_service = ChatService(db)
                result = await chat_service.process_chat(
                    session_id=session_id,
                    user_id=user_id,
                    user_role=user_role,
                    user_message=message,
                    latitude=latitude,
                    longitude=longitude,
                )

                # Stream response characters back to simulate speech synthesis/streaming typing
                text = result["response"]
                for i in range(0, len(text), 10):
                    chunk = text[i:i+10]
                    await websocket.send_json({
                        "event": "chunk",
                        "text": chunk,
                        "session_id": session_id
                    })
                    await asyncio.sleep(0.05)

                await websocket.send_json({
                    "event": "done",
                    "full_response": text,
                    "session_id": session_id,
                    "nearby_assets": result.get("nearby_assets")
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception("Error in WebSocket session loop")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


import json as _json
from pydantic import BaseModel
from app.core.config import settings


class TokenRequest(BaseModel):
    room_name: str
    session_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None


@router.get("/state")
async def get_voice_session_state(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve current voice session state (messages, nearby_assets, active ticket/asset) from Redis."""
    from app.services.memory_service import MemoryService
    async with async_session_maker() as db:
        memory_service = MemoryService(db)
        state = await memory_service.get_session_state(session_id)
        if not state:
            return {
                "messages": [],
                "nearby_assets": [],
                "selected_asset_id": None,
                "active_ticket_id": None,
                "intent": None,
                "data": None,
            }
        
        # Pull database message log if state has them saved or fallback
        history = await memory_service.get_conversation_history(session_id, current_user.id)
        formatted_messages = []
        for i, msg in enumerate(history):
            # We map database messages to UI format
            formatted_messages.append({
                "id": f"msg-{i}",
                "role": msg.get("role"),
                "content": msg.get("content"),
                "timestamp": "",
            })
            
        return {
            "messages": formatted_messages,
            "nearby_assets": state.get("nearby_assets") or [],
            "selected_asset_id": state.get("selected_asset_id"),
            "active_ticket_id": state.get("active_ticket_id"),
            "active_asset_id": state.get("active_asset_id"),
            "intent": state.get("intent"),
            "data": state.get("data"),
        }


@router.post("/token")
async def get_livekit_token(
    req: TokenRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate a LiveKit access token and create the room with agent metadata."""
    if not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LiveKit is not configured. Set LIVEKIT_API_KEY and LIVEKIT_API_SECRET in .env",
        )

    try:
        from livekit import api as lk_api

        # Pre-seed session state in memory service so lat/long is saved before agent joins
        session_id = req.session_id or f"lk_{req.room_name}"
        from app.services.memory_service import MemoryService
        async with async_session_maker() as db:
            memory_service = MemoryService(db)
            state = await memory_service.get_session_state(session_id)
            if not state:
                state = {
                    "messages": [],
                    "session_id": session_id,
                    "user_id": current_user.id,
                    "user_role": current_user.role,
                    "latitude": req.latitude,
                    "longitude": req.longitude,
                    "location_verified": req.latitude is not None,
                    "nearby_assets": [],
                    "selected_asset_id": None,
                    "active_ticket_id": None,
                    "active_asset_id": None,
                    "issue_description": None,
                    "ticket_summary": None,
                    "ticket_id": None,
                    "next_node": "agent",
                    "tickets": None,
                    "intent": None,
                    "data": None,
                    "pending_confirmation": None,
                }
            else:
                if req.latitude is not None:
                    state["latitude"] = req.latitude
                if req.longitude is not None:
                    state["longitude"] = req.longitude
                if req.latitude is not None:
                    state["location_verified"] = True
            await memory_service.save_session_state(session_id, state)

        # Build the room metadata so the agent worker knows which session/user
        room_metadata = _json.dumps({
            "session_id": session_id,
            "user_id": current_user.id,
            "username": current_user.username,
            "user_role": current_user.role,
            "latitude": req.latitude,
            "longitude": req.longitude,
        })

        # Create the room (idempotent) so metadata is attached before agent joins
        lk = lk_api.LiveKitAPI(
            url=settings.LIVEKIT_URL,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
        try:
            await lk.room.create_room(
                lk_api.CreateRoomRequest(name=req.room_name, metadata=room_metadata)
            )
        except Exception:
            pass  # room may already exist — that is fine
        finally:
            await lk.aclose()

        import datetime as _datetime
        # Mint a JWT for the browser participant
        token = (
            lk_api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(f"user-{current_user.id}")
            .with_name(getattr(current_user, "full_name", None) or f"User {current_user.id}")
            .with_grants(lk_api.VideoGrants(room_join=True, room=req.room_name))
            .with_ttl(_datetime.timedelta(hours=1))
        )
        return {
            "token": token.to_jwt(),
            "url": settings.LIVEKIT_URL,
            "room_name": req.room_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate LiveKit token")
        raise HTTPException(status_code=500, detail=str(e))
