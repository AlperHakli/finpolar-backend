from pydantic import BaseModel , Field


class AnalysisModel(BaseModel):
    message: str = Field(default=None , title="Prompt of user")
    session_id: str = Field(default=None , title="Session id of conversation ")
