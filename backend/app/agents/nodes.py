import json
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.state import AgentState
from app.agents.prompts import get_system_prompt
from app.agents.tools import ALL_TOOLS, execute_tool
from app.agents.registry import tool_registry
from app.agents.orchestrator import orchestrator
from app.agents.policy import policy_engine
from app.services.audit_service import AuditService
from app.database.session import async_session_maker
from app.core.logging import logger


async def agent_node(state: AgentState) -> Dict[str, Any]:
    """Main Orchestration Node combining Rule Engine and Configured LLM Provider."""
    logger.info("Executing Agent Orchestration Node", extra={"session_id": state["session_id"]})

    system = get_system_prompt()

    # Inject technician details, active context, and location into system prompt
    context_addon = f"\nTechnician ID: {state['user_id']} (Role: {state['user_role']})"
    if state.get("latitude") is not None and state.get("longitude") is not None:
        context_addon += f"\nLocation: Latitude {state['latitude']}, Longitude {state['longitude']}"
    else:
        context_addon += f"\nLocation: Unavailable (If required for action, ask user for location)."

    if state.get("active_ticket_id"):
        context_addon += f"\nActive Ticket ID in Context: #{state['active_ticket_id']}"
    if state.get("active_asset_id"):
        context_addon += f"\nActive Asset ID in Context: #{state['active_asset_id']}"
    if state.get("selected_asset_id"):
        context_addon += f"\nActive Selected Asset ID: #{state['selected_asset_id']}"

    system += context_addon

    # Execute turn through Hybrid Orchestrator
    response = await orchestrator.orchestrate_turn(state, system, ALL_TOOLS)

    updates = {
        "messages": [{"role": "assistant", "content": response["content"]}]
    }

    # Route to tool execution if tool calls were generated
    if response.get("tool_calls"):
        updates["next_node"] = "execute_tools"
        updates["messages"].append({
            "role": "assistant",
            "content": response.get("content") or "Executing requested tool action...",
            "tool_calls": response["tool_calls"]
        })
    else:
        updates["next_node"] = "end"

    return updates


async def tool_execution_node(state: AgentState) -> Dict[str, Any]:
    """Node responsible for validating policy, executing tools, auditing actions, and updating state."""
    logger.info("Executing Tool Execution Node with Policy Gates", extra={"session_id": state["session_id"]})

    last_message = state["messages"][-1]
    tool_calls = last_message.get("tool_calls", [])

    new_messages = []
    selected_asset_id = state.get("selected_asset_id")
    active_ticket_id = state.get("active_ticket_id")
    active_asset_id = state.get("active_asset_id")
    latitude = state.get("latitude")
    longitude = state.get("longitude")

    intent = state.get("intent")
    data = state.get("data")
    tickets = state.get("tickets")
    nearby_assets = state.get("nearby_assets", [])

    async with async_session_maker.begin() as db:
        audit_service = AuditService(db)

        for tool in tool_calls:
            name = tool["name"]
            args = tool["args"]

            # 1. Policy & Authorization evaluation
            eval_result = policy_engine.evaluate_tool_execution(
                user_role=state["user_role"], tool_name=name, args=args
            )

            if not eval_result["authorized"]:
                err_res = {
                    "success": False,
                    "error": {"code": "UNAUTHORIZED", "message": eval_result["reason"]}
                }
                new_messages.append({
                    "role": "tool",
                    "tool_call_id": tool.get("id"),
                    "name": name,
                    "content": json.dumps(err_res)
                })
                continue

            # 2. Execute backend tool function
            result = await execute_tool(name, args, state["user_id"], db)

            # 3. Log structured audit record
            await audit_service.log_event(
                user_id=state["user_id"],
                session_id=state["session_id"],
                tool_name=name,
                args=args,
                result=result if isinstance(result, dict) else {"success": True},
                authorization=eval_result["reason"]
            )

            # Extract active ticket / asset IDs for conversation memory
            if isinstance(result, dict):
                if "ticket_id" in result:
                    active_ticket_id = result["ticket_id"]
                elif "ticket" in result and isinstance(result["ticket"], dict) and "id" in result["ticket"]:
                    active_ticket_id = result["ticket"]["id"]

                if "asset_id" in result:
                    active_asset_id = result["asset_id"]
                elif "asset" in result and isinstance(result["asset"], dict) and "id" in result["asset"]:
                    active_asset_id = result["asset"]["id"]

                # Map intent and response data payloads for UI components
                if "assets" in result:
                    nearby_assets = result["assets"]
                    intent = "show_assets"
                    data = {"type": "assets", "items": result["assets"], "assets": result["assets"]}
                elif "tickets" in result:
                    tickets = result["tickets"]
                    intent = "show_tickets"
                    data = {"type": "tickets", "items": result["tickets"], "tickets": result["tickets"]}
                elif "ticket" in result:
                    intent = "ticket_detail"
                    data = {"type": "ticket_detail", "ticket": result["ticket"]}

            if name == "get_location" and isinstance(args, dict) and "latitude" in args:
                latitude = args["latitude"]
                longitude = args["longitude"]
                state["location_verified"] = True

            new_messages.append({
                "role": "tool",
                "tool_call_id": tool.get("id"),
                "name": name,
                "content": json.dumps(result)
            })

    return {
        "messages": new_messages,
        "next_node": "agent",
        "latitude": latitude,
        "longitude": longitude,
        "selected_asset_id": selected_asset_id,
        "active_ticket_id": active_ticket_id,
        "active_asset_id": active_asset_id,
        "nearby_assets": nearby_assets,
        "tickets": tickets,
        "intent": intent,
        "data": data,
    }
