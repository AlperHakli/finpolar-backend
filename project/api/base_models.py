from pydantic import BaseModel , Field
from sqlmodel import SQLModel

#langgraph state model
class AnalysisModel(BaseModel):
    message: str = Field(default=None , title="Prompt of user")
    session_id: str = Field(default=None , title="Session id of conversation ")


#database models

class TopVolumeStocksModel(SQLModel , table= True):
    id: int | None = Field(default=None , json_schema_extra={"primary_key":True})
    symbol: str = Field(description="symbol of ticker")
    price: float = Field(description="price of stock")
    trade_value: float = Field(description="trade value of stock")

class MasterTicker(SQLModel , table= True):
    id: int | None = Field(default=None , json_schema_extra={"primary_key":True})
    symbol: str = Field(default=None , json_schema_extra={"primary_key":True})
