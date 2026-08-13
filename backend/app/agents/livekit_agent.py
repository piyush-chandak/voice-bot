"""
LiveKit Gemini Voice Agent Worker
---------------------------------
Runs as a separate process alongside the FastAPI server.

Start with:
    PYTHONPATH=. python -m app.agents.livekit_agent dev

or:
    make agent

AI provider:
    Google Gemini Live API only

Required environment variables:
    LIVEKIT_URL
    LIVEKIT_API_KEY
    LIVEKIT_API_SECRET
    GEMINI_API_KEY
"""

import json
import logging
import os
import sys

logger = logging.getLogger("voice_agent")

# Pre-import all SQLAlchemy models to register them inside mapper collection
try:
    from app.database.models.user import User
    from app.database.models.ticket import Ticket
    from app.database.models.asset import Asset
    from app.database.models.conversation import Conversation
    from app.database.models.memory import Memory
    from app.database.models.audit import Location, AuditLog
except ImportError:
    pass

try:
    from livekit.agents import (
        Agent,
        AgentSession,
        AutoSubscribe,
        JobContext,
        WorkerOptions,
        cli,
        RoomInputOptions,
    )
    from livekit.plugins import google
    LIVEKIT_AVAILABLE = True

except ImportError as e:
    LIVEKIT_AVAILABLE = False
    logger.warning(
        "livekit-agents or livekit-plugins-google is not installed: %s",
        e,
    )


if LIVEKIT_AVAILABLE:

    class TechnicianVoiceAgent(Agent):
        """
        Voice assistant powered entirely by Google Gemini Live API.

        Audio input:
            LiveKit -> Gemini Live API

        LLM:
            Gemini Live API

        Audio output:
            Gemini Live API -> LiveKit
        """

        def __init__(
            self,
            *,
            session_id: str,
            user_id: int,
            user_role: str,
        ) -> None:
            # ---------------------------------------------------------------
            # Define Gemini tools directly on the Agent.
            # ---------------------------------------------------------------
            from livekit.agents import llm
            from app.database.session import async_session_maker

            # Define native tool functions wrapped with llm.function_tool decorator
            # so Gemini Live model can see them in its tool specification.
            
            @llm.function_tool(
                name="find_assets",
                description="Locate nearby assets within a specified geographic radius. If coordinates are not provided, fall back to the cached session location."
            )
            async def find_assets(
                latitude: float | None = None,
                longitude: float | None = None,
                radius_meters: float = 100000.0
            ) -> str:
                """Find nearby equipment assets. If lat/lon are omitted, the tool automatically uses the technician's cached GPS coordinates from the browser. Radius defaults to 100km (100000 meters)."""
                from app.services.memory_service import MemoryService
                
                # Retrieve coordinates from session cache if not provided explicitly by LLM
                actual_lat = latitude
                actual_lon = longitude

                async with async_session_maker() as db:
                    if actual_lat is None or actual_lon is None:
                        memory_service = MemoryService(db)
                        state = await memory_service.get_session_state(session_id) or {}
                        if actual_lat is None:
                            actual_lat = state.get("latitude")
                        if actual_lon is None:
                            actual_lon = state.get("longitude")

                    if actual_lat is None or actual_lon is None:
                        res = {"error": "GPS coordinates are not available yet. Please enable location sharing."}
                        logger.warning("GEMINI VOICE TOOL CALL: find_assets failed (coords missing)")
                        return json.dumps(res)

                    logger.info("GEMINI VOICE TOOL CALL: find_assets (lat=%s, lon=%s, radius=%s)", actual_lat, actual_lon, radius_meters)
                    from app.services.asset_service import AssetService
                    service = AssetService(db)
                    assets = await service.find_nearby_assets(actual_lat, actual_lon, radius_meters)
                    res = {
                        "assets": [
                            {
                                "id": a.id,
                                "name": a.name,
                                "description": a.description,
                                "sku": a.sku,
                                "status": a.status,
                                "latitude": a.latitude,
                                "longitude": a.longitude,
                            }
                            for a in assets
                        ]
                    }
                    logger.info("GEMINI VOICE TOOL RESULT: find_assets -> found %d assets", len(assets))
                    # Save results to Redis session state so frontend updates automatically
                    memory_service = MemoryService(db)
                    state = await memory_service.get_session_state(session_id) or {}
                    state["nearby_assets"] = res["assets"]
                    state["intent"] = "show_assets"
                    state["data"] = {"type": "assets", "items": res["assets"], "assets": res["assets"]}
                    await memory_service.save_session_state(session_id, state)
                    return json.dumps(res)

            @llm.function_tool(
                name="get_asset",
                description="Look up full details of a specific asset by its ID."
            )
            async def get_asset(asset_id: int) -> str:
                """Look up details of a single equipment asset."""
                logger.info("GEMINI VOICE TOOL CALL: get_asset (id=%s)", asset_id)
                from app.services.asset_service import AssetService
                async with async_session_maker() as db:
                    service = AssetService(db)
                    try:
                        a = await service.get_asset(asset_id)
                        res = {
                            "asset": {
                                "id": a.id,
                                "name": a.name,
                                "description": a.description,
                                "sku": a.sku,
                                "status": a.status,
                                "latitude": a.latitude,
                                "longitude": a.longitude,
                            }
                        }
                    except Exception as e:
                        res = {"error": str(e)}
                    logger.info("GEMINI VOICE TOOL RESULT: get_asset -> %s", res)
                    # Save selected asset in Redis session state
                    from app.services.memory_service import MemoryService
                    memory_service = MemoryService(db)
                    state = await memory_service.get_session_state(session_id) or {}
                    state["selected_asset_id"] = asset_id
                    state["active_asset_id"] = asset_id
                    await memory_service.save_session_state(session_id, state)
                    return json.dumps(res)

            @llm.function_tool(
                name="list_tickets",
                description="Retrieve list of all tickets or user's assigned tickets."
            )
            async def list_tickets(my_tickets_only: bool = False) -> str:
                """List work tickets, optionally filtering to the logged-in technician."""
                logger.info("GEMINI VOICE TOOL CALL: list_tickets (my_tickets_only=%s)", my_tickets_only)
                from app.services.ticket_service import TicketService
                async with async_session_maker() as db:
                    service = TicketService(db)
                    if my_tickets_only:
                        tickets = await service.list_my_tickets(user_id)
                    else:
                        tickets = await service.list_tickets()
                    res = {
                        "tickets": [
                            {
                                "id": t.id,
                                "title": t.title,
                                "status": t.status,
                                "priority": t.priority,
                                "asset_id": t.asset_id,
                            }
                            for t in tickets
                        ]
                    }
                    logger.info("GEMINI VOICE TOOL RESULT: list_tickets -> found %d tickets", len(tickets))
                    # Save tickets to Redis session state so frontend updates
                    from app.services.memory_service import MemoryService
                    memory_service = MemoryService(db)
                    state = await memory_service.get_session_state(session_id) or {}
                    state["tickets"] = res["tickets"]
                    state["intent"] = "show_tickets"
                    state["data"] = {"type": "tickets", "items": res["tickets"], "tickets": res["tickets"]}
                    await memory_service.save_session_state(session_id, state)
                    return json.dumps(res)

            @llm.function_tool(
                name="get_ticket",
                description="Look up full details of a specific ticket by its ID."
            )
            async def get_ticket(ticket_id: int) -> str:
                """Retrieve full details and summary of a work ticket."""
                logger.info("GEMINI VOICE TOOL CALL: get_ticket (id=%s)", ticket_id)
                from app.services.ticket_service import TicketService
                async with async_session_maker() as db:
                    service = TicketService(db)
                    try:
                        t = await service.get_ticket(ticket_id)
                        summary = await service.summarize_ticket(ticket_id)
                        res = {
                            "ticket": {
                                "id": t.id,
                                "title": t.title,
                                "description": t.description,
                                "status": t.status,
                                "priority": t.priority,
                                "asset_id": t.asset_id,
                            },
                            "summary": summary
                        }
                    except Exception as e:
                        res = {"error": str(e)}
                    logger.info("GEMINI VOICE TOOL RESULT: get_ticket -> %s", res)
                    # Update active ticket context in Redis
                    from app.services.memory_service import MemoryService
                    memory_service = MemoryService(db)
                    state = await memory_service.get_session_state(session_id) or {}
                    state["active_ticket_id"] = ticket_id
                    state["intent"] = "ticket_detail"
                    state["data"] = {"type": "ticket_detail", "ticket": res.get("ticket")}
                    await memory_service.save_session_state(session_id, state)
                    return json.dumps(res)

            @llm.function_tool(
                name="create_ticket",
                description="Create a new work ticket for a specific asset."
            )
            async def create_ticket(
                title: str,
                description: str,
                asset_id: int,
                priority: str = "medium"
            ) -> str:
                """Create a new work ticket for an asset."""
                logger.info("GEMINI VOICE TOOL CALL: create_ticket (title=%s, asset=%s)", title, asset_id)
                from app.services.ticket_service import TicketService
                async with async_session_maker() as db:
                    service = TicketService(db)
                    try:
                        ticket = await service.create_ticket(
                            title=title,
                            description=description,
                            technician_id=user_id,
                            asset_id=asset_id,
                            priority=priority
                        )
                        await db.commit() # Commit transaction
                        res = {
                            "ticket_id": ticket.id,
                            "title": ticket.title,
                            "status": ticket.status,
                            "priority": ticket.priority,
                            "asset_id": ticket.asset_id,
                            "message": f"Ticket #{ticket.id} created successfully."
                        }
                    except Exception as e:
                        res = {"error": str(e)}
                    logger.info("GEMINI VOICE TOOL RESULT: create_ticket -> %s", res)
                    return json.dumps(res)

            @llm.function_tool(
                name="complete_service",
                description="Mark a ticket status as completed when repair is done."
            )
            async def complete_service(ticket_id: int) -> str:
                """Mark service on a ticket as completed and commit database transaction."""
                logger.info("GEMINI VOICE TOOL CALL: complete_service (id=%s)", ticket_id)
                from app.services.ticket_service import TicketService
                async with async_session_maker() as db:
                    service = TicketService(db)
                    try:
                        t = await service.complete_service(ticket_id)
                        await db.commit() # Commit transaction
                        res = {
                            "ticket_id": t.id,
                            "status": t.status,
                            "message": f"Service on Ticket #{t.id} completed."
                        }
                    except Exception as e:
                        res = {"error": str(e)}
                    logger.info("GEMINI VOICE TOOL RESULT: complete_service -> %s", res)
                    return json.dumps(res)

            super().__init__(
                instructions=(
                    "You are a helpful field technician voice assistant. "
                    "You work with real equipment asset and ticket data from the database. "
                    "GPS coordinates are automatically retrieved from the technician's browser session. "
                    "When the technician asks to find, list, or check assets, IMMEDIATELY call `find_assets()` WITHOUT parameters. "
                    "Do NOT ask the technician for coordinates, latitude, longitude, or search radius. "
                    "CRITICAL DATABASE RULES: "
                    "Never invent, assume, or hallucinate database records. "
                    "Always execute the appropriate database tool to lookup assets or tickets. "
                    "If a lookup tool returns no records, inform the user that no records were found. "
                    "If a database tool fails, state that the lookup failed. "
                    "Be highly concise because this is a real-time voice conversation.\n"
                    "OFF-TOPIC REFUSAL RULE: "
                    "If the user asks a question that does not directly map to one of your available tools "
                    "(such as general knowledge, weather, off-topic requests, or tasks not covered by find_assets, get_asset, list_tickets, get_ticket, create_ticket, or complete_service), "
                    "you MUST politely refuse and reply exactly that you cannot answer it right now or that you only support asset and ticket operations."
                ),
                tools=[
                    find_assets,
                    get_asset,
                    list_tickets,
                    get_ticket,
                    create_ticket,
                    complete_service,
                ]
            )

            self.session_id = session_id
            self.user_id = user_id
            self.user_role = user_role

        # Removed user turn interception to let Gemini call tools natively.


    async def entrypoint(ctx: JobContext) -> None:
        logger.info(
            "Gemini voice agent starting — room: %s",
            ctx.room.name,
        )

        await ctx.connect(
            auto_subscribe=AutoSubscribe.AUDIO_ONLY,
        )

        # ---------------------------------------------------------------
        # Read metadata written by your token endpoint.
        # ---------------------------------------------------------------

        meta_raw = ctx.room.metadata or "{}"

        try:
            meta = json.loads(meta_raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning(
                "Invalid room metadata: %s",
                meta_raw,
            )
            meta = {}

        session_id = meta.get(
            "session_id",
            f"lk_{ctx.room.name}",
        )

        try:
            user_id = int(
                meta.get("user_id", 1)
            )
        except (TypeError, ValueError):
            user_id = 1

        user_role = meta.get(
            "user_role",
            "Technician",
        )

        logger.info(
            "Room metadata — session_id=%s user_id=%s role=%s",
            session_id,
            user_id,
            user_role,
        )

        # ---------------------------------------------------------------
        # Gemini API authentication
        # ---------------------------------------------------------------

        gemini_key = os.getenv("GEMINI_API_KEY")

        if not gemini_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        # livekit.plugins.google uses GOOGLE_API_KEY for Gemini API.
        os.environ["GOOGLE_API_KEY"] = gemini_key

        # ---------------------------------------------------------------
        # Create our technician agent.
        # ---------------------------------------------------------------

        agent = TechnicianVoiceAgent(
            session_id=session_id,
            user_id=user_id,
            user_role=user_role,
        )

        # ---------------------------------------------------------------
        # Gemini Live API
        #
        # This replaces:
        #   - Google Cloud STT
        #   - separate LLM
        #   - Google Cloud TTS
        #   - Deepgram
        #
        # Gemini handles the realtime voice conversation itself.
        # ---------------------------------------------------------------

        # Extract coordinates from metadata
        lat = meta.get("latitude")
        lon = meta.get("longitude")
        username = meta.get("username", "Technician")
        location_instructions = ""
        if lat is not None and lon is not None:
            location_instructions = f" The technician's current location is Latitude: {lat}, Longitude: {lon}. Use this location context when looking up nearby assets or tickets."
        else:
            location_instructions = " The technician's GPS coordinates are currently unavailable. Ask them for location access or coords if nearby data is required."

        # Save location in session cache immediately on connect so it's globally available
        from app.database.session import async_session_maker
        from app.services.memory_service import MemoryService
        async with async_session_maker() as db:
            memory_service = MemoryService(db)
            state = await memory_service.get_session_state(session_id) or {}
            if lat is not None:
                state["latitude"] = lat
            if lon is not None:
                state["longitude"] = lon
            state["location_verified"] = lat is not None
            await memory_service.save_session_state(session_id, state)



        session = AgentSession(
            llm=google.realtime.RealtimeModel(
                voice="Puck",
                temperature=0.2,
                instructions=(
                    "You are a helpful field technician voice assistant. "
                    "Keep answers short and conversational. "
                    "Speak naturally and clearly. "
                    "Prioritize actionable information for technicians."
                    + location_instructions
                    + " If the user asks a question that does not directly map to one of your available tools (such as general knowledge, weather, off-topic requests, or tasks not covered by find_assets, get_asset, list_tickets, get_ticket, create_ticket, or complete_service), you MUST politely refuse and reply exactly that you cannot answer it right now or that you only support asset and ticket operations."
                ),
            ),
        )

        # ---------------------------------------------------------------
        # Speech & Processing State Logging Events
        # ---------------------------------------------------------------
        import time

        class TimingState:
            user_stop_time: float = 0.0

        timing = TimingState()

        @session.on("user_started_speaking")
        def on_user_started_speaking():
            logger.info("LOG EVENT: User started speaking...")

        @session.on("user_stopped_speaking")
        def on_user_stopped_speaking():
            timing.user_stop_time = time.time()
            logger.info("LOG EVENT: User stopped speaking. Initiating model reasoning/STT...")

        @session.on("agent_started_speaking")
        def on_agent_started_speaking():
            delay = ""
            if timing.user_stop_time > 0:
                elapsed = time.time() - timing.user_stop_time
                delay = f" (Took {elapsed:.2f}s to process turn and synthesize speech)"
                timing.user_stop_time = 0.0
            logger.info("LOG EVENT: Agent started speaking / playing TTS output%s...", delay)

        @session.on("agent_stopped_speaking")
        def on_agent_stopped_speaking():
            logger.info("LOG EVENT: Agent stopped speaking. Back to listening mode.")

        # ---------------------------------------------------------------
        # Start the Gemini voice session.
        # ---------------------------------------------------------------

        await session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(),
        )

        logger.info(
            "Gemini Live session started — room=%s",
            ctx.room.name,
        )

        # ---------------------------------------------------------------
        # Initial greeting
        # ---------------------------------------------------------------

        await session.generate_reply(
            instructions=(
                f"Greet the user as: Hi {username}. Introduce yourself as their Voice Technician Assistant. "
                "Briefly explain that you can help them locate nearby assets at their current location, "
                "check details of tickets assigned to them, update ticket statuses, or raise new tickets for assets. "
                "Ask how you can assist them today."
            ),
        )


def run() -> None:
    """
    Entry point:

        python -m app.agents.livekit_agent dev
    """

    if not LIVEKIT_AVAILABLE:
        sys.exit(
            "LiveKit Agents is not installed. "
            "Install it with: "
            "pip install 'livekit-agents[google]'"
        )

    # ---------------------------------------------------------------
    # Load environment variables.
    # ---------------------------------------------------------------

    from dotenv import load_dotenv

    load_dotenv("backend/.env")
    load_dotenv(".env")

    livekit_url = os.getenv(
        "LIVEKIT_URL",
        "ws://localhost:7880",
    )

    livekit_api_key = os.getenv(
        "LIVEKIT_API_KEY",
        "devkey",
    )

    livekit_api_secret = os.getenv(
        "LIVEKIT_API_SECRET",
        "secret",
    )

    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key:
        sys.exit(
            "GEMINI_API_KEY is missing. "
            "Add it to backend/.env or .env."
        )

    # Gemini's LiveKit Google plugin expects GOOGLE_API_KEY.
    os.environ["GOOGLE_API_KEY"] = gemini_key

    logger.info(
        "Starting Gemini LiveKit agent — url=%s",
        livekit_url,
    )

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=livekit_url,
            api_key=livekit_api_key,
            api_secret=livekit_api_secret,
        )
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    run()