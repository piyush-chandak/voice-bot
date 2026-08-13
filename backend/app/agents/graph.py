from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes import agent_node, tool_execution_node

# Create and compile the StateGraph workflow
workflow = StateGraph(AgentState)

# Register graph nodes
workflow.add_node("agent", agent_node)
workflow.add_node("execute_tools", tool_execution_node)

# Define entry point
workflow.set_entry_point("agent")


def route_next(state: AgentState) -> str:
    """Routes the execution based on the next_node attribute in the state."""
    next_node = state.get("next_node", "end")
    if next_node == "execute_tools":
        return "execute_tools"
    return "end"


# Set conditional routing edges
workflow.add_conditional_edges(
    "agent",
    route_next,
    {
        "execute_tools": "execute_tools",
        "end": END,
    },
)

# Loop back to agent after tool execution to report findings
workflow.add_edge("execute_tools", "agent")

compiled_graph = workflow.compile()
