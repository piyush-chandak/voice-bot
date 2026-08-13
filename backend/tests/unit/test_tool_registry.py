import pytest
from app.agents.registry import ToolRegistry


@pytest.mark.asyncio
async def test_tool_registry_registration_and_execution():
    registry = ToolRegistry()

    @registry.register(
        name="test_tool",
        description="A test tool function",
        input_schema={
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
        },
    )
    async def sample_tool(value: str, user_id: int = None):
        return {"result": f"hello {value}", "user": user_id}

    schemas = registry.get_schemas()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "test_tool"

    output = await registry.execute_tool("test_tool", {"value": "world"}, user_id=42, db=None)
    assert output["result"] == "hello world"
    assert output["user"] == 42


@pytest.mark.asyncio
async def test_tool_registry_unknown_tool():
    registry = ToolRegistry()
    output = await registry.execute_tool("non_existent_tool", {}, user_id=1, db=None)
    assert "error" in output
    assert "not found" in output["error"]


@pytest.mark.asyncio
async def test_tool_registry_exception_handling():
    registry = ToolRegistry()

    @registry.register(
        name="failing_tool",
        description="A tool that raises an exception",
        input_schema={"type": "object", "properties": {}},
    )
    async def failing_tool():
        raise ValueError("Simulated tool failure")

    output = await registry.execute_tool("failing_tool", {}, user_id=1, db=None)
    assert "error" in output
    assert output["details"] == "Simulated tool failure"
