from pydantic import BaseModel
from sqlmodel import SQLModel , Field

#langgraph state model
class AnalysisModel(BaseModel):
    message: str = Field(default=None , title="Prompt of user")
    session_id: str = Field(default=None , title="Session id of conversation ")


#fastapi get single stock indicator model

class GetSingleStockIndicatorModel(BaseModel):
    rsi_period: int = 14  # period for rsi
    bb_period: int = 20  # period for bollinger
    bb_std_dev: int = 2  # Bollinger standart deviation
    ma_short: int = 20  # MA short
    ma_long: int = 50  # MA long
    macd_fast: int = 12  # MACD fast
    macd_slow: int = 26  # MACD slow
    macd_signal: int = 9  # MACD signal


#database models

class TopVolumeStocksModel(SQLModel , table= True):
    id: int | None = Field(default=None , primary_key= True)
    symbol: str = Field(description="symbol of ticker")
    price: float = Field(description="price of stock")
    trade_value: float = Field(description="trade value of stock")
    changePercent: float = Field(description="Change percent between prev close and current close")

class MasterTicker(SQLModel , table= True):
    id: int | None = Field(default=None , primary_key = True)
    symbol: str = Field(default=None)
