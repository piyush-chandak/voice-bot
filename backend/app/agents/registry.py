import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger


class ToolRegistry:
    """Centralized Tool Registry supporting dynamic discovery, metadata, policy validation, and auditability."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        category: str = "general",
        read_only: bool = True,
        risk_level: str = "low",
        requires_confirmation: bool = False,
        requires_authorization: bool = True,
        output_schema: Optional[Dict[str, Any]] = None,
    ):
        """Register a domain tool with full enterprise metadata."""

        def decorator(func: Callable):
            self._tools[name] = {
                "name": name,
                "description": description,
                "input_schema": input_schema,
                "output_schema": output_schema or {},
                "category": category,
                "read_only": read_only,
                "risk_level": risk_level,
                "requires_confirmation": requires_confirmation,
                "requires_authorization": requires_authorization,
                "func": func,
            }
            return func

        return decorator

    def get_schemas(self, user_role: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return tool definitions in standard JSON schema format for LLM reasoning."""
        return [
            {
                "name": info["name"],
                "description": info["description"],
                "input_schema": info["input_schema"],
                "category": info["category"],
                "read_only": info["read_only"],
                "risk_level": info["risk_level"],
                "requires_confirmation": info["requires_confirmation"],
            }
            for info in self._tools.values()
        ]

    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get registered metadata for a specific tool."""
        return self._tools.get(name)

    def list_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Return registered tools belonging to a category."""
        return [t for t in self._tools.values() if t["category"] == category]

    async def execute_tool(
        self, name: str, args: Dict[str, Any], user_id: int, db: AsyncSession
    ) -> Dict[str, Any]:
        """Validate, log, execute a tool function, and return standardized response contract."""
        if name not in self._tools:
            logger.error(f"Tool execution failed: '{name}' is not registered.")
            return {
                "success": False,
                "error": f"Tool '{name}' not found",
                "name": name,
                "metadata": {"tool_name": name},
            }

        tool_info = self._tools[name]
        func = tool_info["func"]

        logger.info(
            f"Executing AI domain tool: '{name}' [Category: {tool_info['category']}, Risk: {tool_info['risk_level']}]",
            extra={"tool_name": name, "tool_args": args, "user_id": user_id},
        )

        try:
            sig = inspect.signature(func)
            kwargs = dict(args)
            if "user_id" in sig.parameters:
                kwargs["user_id"] = user_id
            if "db" in sig.parameters:
                kwargs["db"] = db

            if asyncio.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)

            # Preserve backward compatibility if tool already returns keys directly
            if isinstance(result, dict):
                result["success"] = True if "error" not in result else False
                result["metadata"] = {"tool_name": name, "category": tool_info["category"]}
                return result

            return {
                "success": True,
                "data": result,
                "error": None,
                "metadata": {"tool_name": name, "category": tool_info["category"]},
            }

        except Exception as e:
            logger.exception(f"Error occurred while executing tool '{name}': {str(e)}")
            return {
                "success": False,
                "error": f"Failed to execute operation '{name}'",
                "details": str(e),
                "metadata": {"tool_name": name},
            }


tool_registry = ToolRegistry()
