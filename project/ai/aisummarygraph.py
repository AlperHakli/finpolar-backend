from langgraph.graph import StateGraph , END
from langgraph.checkpoint.memory import MemorySaver
from project.ai.data_models import SummaryAgentState
from project.ai.tools import custom_tool_executor
from project.ai.nodes import call_model , should_continue , call_summary_model

memory = MemorySaver()

ai_summary_workflow = StateGraph(SummaryAgentState)

ai_summary_workflow.add_node("agent" , call_model)

ai_summary_workflow.add_node("tool_node" , custom_tool_executor)

ai_summary_workflow.add_node("formatter_node" , call_summary_model)

ai_summary_workflow.set_entry_point("agent")

ai_summary_workflow.add_conditional_edges(
    "agent",
    should_continue,
    path_map={
        "action":"tool_node",
        END:"formatter_node"
    }
)
ai_summary_workflow.add_edge("formatter_node" , END)
ai_summary_workflow.add_edge("tool_node" , "agent")


summary_app = ai_summary_workflow.compile(checkpointer=memory)

