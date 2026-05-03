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


#base stat model
class StatBase(SQLModel):
    # -- Constant features --
    id: int | None = Field(default=None , primary_key = True)
    # -- Updated only once --
    symbol: str = Field(index=True,default="none",unique=True)
    name:str = Field(default="none")

    # updates daily
    previous_close: float = Field(default=0.0 , description="previous close value")

    #updates one time in 3 days
    marketCap: float = Field(default=0.0)
    year_high:float = Field(default=0.0 , description="highest price in current year")
    year_low: float = Field(default=0.0 , description="lowest price in current year")


#stock stats model
class StockStats(StatBase , table= True):
    # -- Constant features --
    # -- Dynamic features --
    trailingPE: float = Field(default=0.0)
    #updated one time in 7 days
    sector: str = Field(default="none")
    summary: str = Field(default="none")
    eps: float = Field(default= 0.0)
