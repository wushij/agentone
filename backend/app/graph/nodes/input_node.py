"""backend/app/graph/nodes/input_node.py"""

from langchain_core.messages import HumanMessage

from app.graph.state import AgentState


async def input_node(state: AgentState) -> dict:
    user_input = (state.get("user_input") or "").strip()
    if not user_input:
        return {"error": "用户输入不能为空", "current_node": "input"}
    return {
        "user_input": user_input,
        "messages": [HumanMessage(content=user_input)],
        "current_node": "input",
        "metadata": {"input_length": len(user_input)},
    }
