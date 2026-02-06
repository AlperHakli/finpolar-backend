from langgraph.graph import StateGraph , END
from langgraph.checkpoint.memory import MemorySaver
from project.ai.agentstate import AgentState
from project.ai.tools import custom_tool_executor
from project.ai.nodes import call_model , should_continue

workflow = StateGraph(AgentState)

memory = MemorySaver();


workflow.add_node("agent" , call_model)

workflow.add_node("tool_node" , custom_tool_executor)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "action" : "tool_node",
        END : END
    }
)

workflow.add_edge("tool_node" , "agent")

app = workflow.compile(checkpointer=memory)


