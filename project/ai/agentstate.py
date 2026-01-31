from typing import Annotated , TypedDict , Optional
from langgraph.graph.message import add_messages
import polars as pl

class AgentState(TypedDict):
    messages : Annotated[list , add_messages]
    raw_data : Optional[pl.DataFrame]
