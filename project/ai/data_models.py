from typing import Annotated, TypedDict, Optional
from langgraph.graph.message import add_messages
from pydantic import BaseModel , Field
import polars as pl


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    raw_data: Optional[pl.DataFrame]

class OutputParserModel(BaseModel):
    score: int = Field(description="final technical analysis score between 1 and 100")

class SummaryAgentState(TypedDict):
    messages: Annotated[list , add_messages]
    final_score : int | None



