from langchain_core.messages import ToolMessage
from project.ai.data_models import AgentState
from project.ai.model import basemodel
from project.ai.tools import get_stock
from langgraph.graph import END
from project.ai.prompts import SYSTEM_MESSAGE
from project.logic.constants import ALL_TOOLS
async def call_model(state: AgentState):
    messages = state.get("messages" , [])

    window_size = 10
    if len(messages) > window_size:
        limited_history = messages[-window_size:]
        while limited_history and (
                isinstance(limited_history[0], ToolMessage) or
                (hasattr(limited_history[0], "tool_calls") and not limited_history[0].content and limited_history[
                    0].tool_calls)
        ):
            limited_history.pop(0)
    else:
        limited_history = messages

    last_message = messages[-1] if messages else None


    if isinstance(last_message, ToolMessage) and "Error" in last_message.content:
        response = basemodel.invoke([SYSTEM_MESSAGE] + limited_history)
        return {"messages": [response]}


    raw_data = state.get("raw_data")

    if raw_data is None:
        model_with_tools = basemodel.bind_tools([get_stock])
    else:
        model_with_tools = basemodel.bind_tools(ALL_TOOLS)

    response = await model_with_tools.ainvoke([SYSTEM_MESSAGE] + limited_history)

    return {"messages" : [response]}

def should_continue(state: AgentState):
    messages = state["messages"]

    last_message = messages[-1]

    if last_message.tool_calls:
        return "action"
    return END
