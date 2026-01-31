from project.ai.agentstate import AgentState
from project.ai.model import basemodel
from project.ai.tools import all_tools , only_get_stock_tool
from langgraph.graph import END
def call_model(state: AgentState):
    messages = state.get("messages")

    raw_data = state.get("raw_data")

    if raw_data is None:
        model_with_tools = basemodel.bind_tools(only_get_stock_tool)
    else:
        model_with_tools = basemodel.bind_tools(all_tools)

    response = model_with_tools.invoke(messages)

    return {"messages" : [response]}


def should_continue(state: AgentState):
    messages = state["messages"]

    last_message = messages[-1]

    if last_message.tool_calls:
        return "action"
    return END
