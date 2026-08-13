import json
from typing import Any, Dict, List, Optional
from app.services.memory_service import MemoryService
from app.database.session import async_session_maker
from app.core.logging import logger
from app.integrations.base_llm import get_llm_provider
from app.agents.tools import ALL_TOOLS, execute_tool


class ChatService:
    def __init__(self):
        pass

    async def process_chat(
        self,
        session_id: str,
        user_id: int,
        user_role: str,
        user_message: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        selected_asset_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        logger.info("Processing technician conversation turn via unified tool agent", extra={"session_id": session_id})

        # 1. Retrieve session state from Redis (short-term memory)
        async with async_session_maker() as db:
            memory_service = MemoryService(db)
            state = await memory_service.get_session_state(session_id)

        if not state:
            state = {
                "session_id": session_id,
                "user_id": user_id,
                "user_role": user_role,
                "latitude": latitude,
                "longitude": longitude,
                "location_verified": latitude is not None,
                "nearby_assets": [],
                "selected_asset_id": selected_asset_id,
                "active_ticket_id": None,
                "active_asset_id": selected_asset_id,
                "tickets": None,
                "intent": None,
                "data": None,
            }
        else:
            # Overwrite lat/lon/asset if provided in request
            if latitude is not None:
                state["latitude"] = latitude
            if longitude is not None:
                state["longitude"] = longitude
            if selected_asset_id is not None:
                state["selected_asset_id"] = selected_asset_id
                state["active_asset_id"] = selected_asset_id

            # Clear transient state fields from previous turn
            state["intent"] = None
            state["data"] = None
            state["tickets"] = None
            state["nearby_assets"] = []

        # 2. Append User input to database (long-term memory)
        async with async_session_maker.begin() as db:
            memory_service = MemoryService(db)
            history = await memory_service.get_conversation_history(session_id, user_id)
            await memory_service.append_message(session_id, user_id, "user", user_message)

        # 3. Formulate the system instructions with off-topic refusal constraint
        system_prompt = (
            "You are a helpful field technician voice assistant. "
            "You work with real equipment asset and ticket data from the database. "
            "GPS coordinates are automatically retrieved from the technician's browser session. "
            "When the technician asks to find, list, or check assets, IMMEDIATELY call `find_assets` WITHOUT parameters. "
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
        )

        # Format coordinates/context
        lat = state.get("latitude")
        lon = state.get("longitude")
        if lat is not None and lon is not None:
            system_prompt += f"\nTechnician ID: {user_id} (Role: {user_role})\nLocation: Latitude {lat}, Longitude {lon}"
        else:
            system_prompt += f"\nTechnician ID: {user_id} (Role: {user_role})\nLocation: Unavailable (If required for action, ask user for location)."

        if state.get("active_ticket_id"):
            system_prompt += f"\nActive Ticket ID in Context: #{state['active_ticket_id']}"
        if state.get("active_asset_id"):
            system_prompt += f"\nActive Asset ID in Context: #{state['active_asset_id']}"

        # 4. Construct messages list for LLM (mapping DB roles to LLM roles)
        formatted_messages = []
        for msg in history:
            role = msg.get("role")
            content = msg.get("content")
            if role in ("user", "assistant"):
                formatted_messages.append({"role": role, "content": content})
        # Add current user message
        formatted_messages.append({"role": "user", "content": user_message})

        # Filter to only the 6 core tools
        core_tool_names = {"find_assets", "get_asset", "list_tickets", "get_ticket", "create_ticket", "complete_service"}
        tools = [t for t in ALL_TOOLS if t["name"] in core_tool_names]

        # 5. Execute LLM + tool execution loop
        provider = get_llm_provider()
        max_iterations = 5
        iteration = 0
        response_text = ""
        intent = None
        json_data = None

        while iteration < max_iterations:
            iteration += 1
            response = await provider.generate_message(
                messages=formatted_messages,
                system_prompt=system_prompt,
                tools=tools,
                temperature=0.0
            )

            response_text = response.get("content") or ""
            tool_calls = response.get("tool_calls") or []

            if not tool_calls:
                break

            # Append the assistant message with tool calls to history
            formatted_messages.append({
                "role": "assistant",
                "content": response_text,
                "tool_calls": tool_calls
            })

            # Execute tool calls
            async with async_session_maker.begin() as db:
                for tc in tool_calls:
                    tc_name = tc["name"]
                    tc_args = tc["args"]
                    tc_id = tc.get("id")

                    # Handle location coordinates fallback if omitted by model
                    if tc_name == "find_assets":
                        if "latitude" not in tc_args or tc_args["latitude"] is None:
                            tc_args["latitude"] = lat
                        if "longitude" not in tc_args or tc_args["longitude"] is None:
                            tc_args["longitude"] = lon

                    tool_result = await execute_tool(tc_name, tc_args, user_id, db)

                    # Update internal state tracking based on tool outputs
                    if isinstance(tool_result, dict):
                        if "ticket_id" in tool_result:
                            state["active_ticket_id"] = tool_result["ticket_id"]
                        elif "ticket" in tool_result and isinstance(tool_result["ticket"], dict) and "id" in tool_result["ticket"]:
                            state["active_ticket_id"] = tool_result["ticket"]["id"]

                        if "asset_id" in tool_result:
                            state["active_asset_id"] = tool_result["asset_id"]
                            state["selected_asset_id"] = tool_result["asset_id"]
                        elif "asset" in tool_result and isinstance(tool_result["asset"], dict) and "id" in tool_result["asset"]:
                            state["active_asset_id"] = tool_result["asset"]["id"]
                            state["selected_asset_id"] = tool_result["asset"]["id"]

                        if "assets" in tool_result:
                            state["nearby_assets"] = tool_result["assets"]
                            intent = "show_assets"
                            json_data = {"type": "assets", "items": tool_result["assets"], "assets": tool_result["assets"]}
                        elif "tickets" in tool_result:
                            state["tickets"] = tool_result["tickets"]
                            intent = "show_tickets"
                            json_data = {"type": "tickets", "items": tool_result["tickets"], "tickets": tool_result["tickets"]}
                        elif "ticket" in tool_result:
                            intent = "ticket_detail"
                            json_data = {"type": "ticket_detail", "ticket": tool_result["ticket"]}

                    # Append tool result to LLM turn conversation
                    formatted_messages.append({
                        "role": "tool",
                        "name": tc_name,
                        "tool_call_id": tc_id,
                        "content": json.dumps(tool_result)
                    })

        # 6. Save Assistant response to long-term and short-term memory
        if response_text:
            async with async_session_maker.begin() as db:
                memory_service = MemoryService(db)
                await memory_service.append_message(session_id, user_id, "assistant", response_text)

        # Save to Redis
        async with async_session_maker() as db:
            memory_service = MemoryService(db)
            await memory_service.save_session_state(session_id, state)

        return {
            "response": response_text or "How can I help you today?",
            "session_id": session_id,
            "latitude": state.get("latitude"),
            "longitude": state.get("longitude"),
            "selected_asset_id": state.get("selected_asset_id"),
            "active_ticket_id": state.get("active_ticket_id"),
            "active_asset_id": state.get("active_asset_id"),
            "intent": intent,
            "data": json_data,
        }
