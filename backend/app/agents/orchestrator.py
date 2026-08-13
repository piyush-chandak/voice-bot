import re
from typing import Any, Dict, List, Optional
from app.core.logging import logger
from app.integrations.base_llm import get_llm_provider


class HybridOrchestrator:
    """Hybrid AI + Rule Engine Orchestrator routing deterministic queries vs LLM reasoning."""

    def __init__(self):
        pass

    def classify_intent_rules(self, message: str, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate deterministic rules to generate direct tool calls without needing an LLM call."""
        text = message.strip().lower()
        lat = state.get("latitude")
        lon = state.get("longitude")
        active_asset_id = state.get("active_asset_id") or state.get("selected_asset_id")
        active_ticket_id = state.get("active_ticket_id")

        # Rule 1: Geolocation nearby assets
        if ("asset" in text or "equipment" in text or "pump" in text or "transformer" in text) and ("near" in text or "around" in text or "closest" in text):
            if lat is not None and lon is not None:
                return {
                    "is_deterministic": True,
                    "intent": "FIND_NEARBY_ASSETS",
                    "content": "Searching for nearby assets around your current location...",
                    "tool_calls": [{
                        "id": "rule_find_assets",
                        "name": "find_assets",
                        "args": {"latitude": lat, "longitude": lon, "radius_meters": 500.0}
                    }]
                }

        # Rule 2: Geolocation nearby tickets
        if ("ticket" in text or "job" in text or "work order" in text) and ("near" in text or "around" in text or "closest" in text):
            if lat is not None and lon is not None:
                return {
                    "is_deterministic": True,
                    "intent": "FIND_NEARBY_TICKETS",
                    "content": "Locating open service tickets near your current GPS position...",
                    "tool_calls": [{
                        "id": "rule_find_tickets",
                        "name": "find_nearby_tickets",
                        "args": {"latitude": lat, "longitude": lon, "radius_meters": 1000.0}
                    }]
                }

        # Rule 3: Tickets for selected asset
        if ("ticket" in text or "tickets" in text) and ("selected" in text or "this asset" in text or "current asset" in text):
            if active_asset_id:
                return {
                    "is_deterministic": True,
                    "intent": "GET_ASSET_TICKETS",
                    "content": f"Retrieving open work tickets associated with Asset #{active_asset_id}...",
                    "tool_calls": [{
                        "id": "rule_asset_tickets",
                        "name": "search_tickets",
                        "args": {"asset_id": active_asset_id}
                    }]
                }

        # Rule 4: Show technician's own assigned tickets
        if "my tickets" in text or "assigned to me" in text or "my open tickets" in text:
            return {
                "is_deterministic": True,
                "intent": "GET_MY_TICKETS",
                "content": "Fetching work tickets assigned to you...",
                "tool_calls": [{
                    "id": "rule_my_tickets",
                    "name": "list_tickets",
                    "args": {"my_tickets_only": True, "skip": 0, "limit": 20}
                }]
            }

        # Rule 5: Mark active ticket complete
        if ("mark" in text or "close" in text or "complete" in text or "done" in text or "fixed" in text) and ("ticket" in text or "it" in text or "issue" in text):
            # Extract ticket ID if present in text
            match = re.search(r"ticket\s*#?(\d+)", text)
            target_ticket_id = int(match.group(1)) if match else active_ticket_id
            if target_ticket_id:
                return {
                    "is_deterministic": True,
                    "intent": "COMPLETE_TICKET",
                    "content": f"Initiating status update for Ticket #{target_ticket_id} to completed.",
                    "tool_calls": [{
                        "id": "rule_complete_ticket",
                        "name": "update_ticket_status",
                        "args": {"ticket_id": target_ticket_id, "status": "completed"}
                    }]
                }

        return None

    async def orchestrate_turn(
        self, state: Dict[str, Any], system_prompt: str, tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Orchestrate conversation turn: evaluate deterministic rules first, fallback to configured LLM Provider."""
        messages = state.get("messages", [])
        
        # Only evaluate deterministic rules if the latest message is directly from the user
        if messages and messages[-1].get("role") == "user":
            last_message = messages[-1].get("content", "")
            rule_result = self.classify_intent_rules(last_message, state)
            if rule_result:
                logger.info(f"Deterministic Rule Engine matched intent: {rule_result['intent']}")
                return {
                    "content": rule_result["content"],
                    "tool_calls": rule_result["tool_calls"],
                    "provider": "rule_engine"
                }

        # Fallback to configured LLM Provider for reasoning
        provider = get_llm_provider()
        logger.info(f"Routing turn to configured LLM Provider: {provider.provider_name}")
        response = await provider.generate_message(
            messages=messages,
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.0
        )
        response["provider"] = provider.provider_name
        return response


orchestrator = HybridOrchestrator()
