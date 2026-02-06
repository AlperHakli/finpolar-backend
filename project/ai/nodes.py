from langchain_core.messages import ToolMessage
from project.ai.agentstate import AgentState
from project.ai.model import basemodel
from project.ai.tools import all_tools , only_get_stock_tool
from langgraph.graph import END
from project.ai.prompts import SYSTEM_MESSAGE
def call_model(state: AgentState):
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
        model_with_tools = basemodel.bind_tools(only_get_stock_tool)
    else:
        model_with_tools = basemodel.bind_tools(all_tools)

    response = model_with_tools.invoke([SYSTEM_MESSAGE] + limited_history)

    return {"messages" : [response]}

def should_continue(state: AgentState):
    messages = state["messages"]

    last_message = messages[-1]

    if last_message.tool_calls:
        return "action"
    return END
