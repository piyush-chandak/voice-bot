from typing import Any, Dict, Optional
from app.agents.registry import tool_registry
from app.core.logging import logger


class PolicyEngine:
    """Enterprise Policy & Security Engine enforcing Role-Based Access Control and risk confirmation gates."""

    @staticmethod
    def evaluate_tool_execution(
        user_role: str, tool_name: str, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if user role is authorized to execute a tool and determine confirmation requirements."""
        tool_info = tool_registry.get_tool_info(tool_name)
        if not tool_info:
            return {
                "authorized": False,
                "requires_confirmation": False,
                "reason": f"Tool '{tool_name}' is not registered in security policy",
            }

        # Role-based tool restrictions
        role = (user_role or "Technician").lower()
        risk_level = tool_info.get("risk_level", "low")

        # Admin has full access
        if role == "admin":
            return {
                "authorized": True,
                "requires_confirmation": tool_info.get("requires_confirmation", False),
                "reason": "Authorized (Admin Role)",
            }

        # Technician role policy rules
        if role in ["technician", "field_service", "user"]:
            # High-risk write operations enforce confirmation
            requires_conf = tool_info.get("requires_confirmation", False) or risk_level == "high"
            return {
                "authorized": True,
                "requires_confirmation": requires_conf,
                "reason": "Authorized (Technician Role)",
            }

        return {
            "authorized": False,
            "requires_confirmation": False,
            "reason": f"Role '{user_role}' is not authorized to execute tool '{tool_name}'",
        }


policy_engine = PolicyEngine()
