from typing import Any

from pydantic import BaseModel , field_validator
from sqlmodel import SQLModel, Field

#langgraph state model
class AnalysisModel(BaseModel):
    message: str = Field(default=None, title="Prompt of user")
    session_id: str = Field(default=None, title="Session id of conversation ")


#fastapi get single stock indicator model
# TODO veritabanı none hatasını çöz frontend ayarlamalarını yap
class GetSingleStockIndicatorModel(BaseModel):
    ticker: str  # asset code
    period: str  # main period
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
    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, default="none", unique=True)
    name: str = Field(default="none")

    # updates daily
    previousClose: float | None = Field(default=0.0, description="previous close value")
    dayHigh: float | None = Field(default=0.0, description="highest price of yesterday")
    dayLow: float | None = Field(default=0.0, description="lowest price of yesterday")
    volume: float | None = Field(default=0.0, description="volume of stock")
    open: float | None = Field(default=0.0, description="open price of asset")
    marketCap: float | None = Field(default=0.0, description="market capacity of asset")

    lastVolume: float | None = Field(default=0.0 , description="daily volume of asset")
    avgVolume10Days: float | None = Field(default=0.0, description="average volume of last 10 days")
    avg50Days: float | None = Field(default=0.0, description="average volume of last 50 days")
    avgVolume3Months: float | None = Field(default=0.0, description="average volume of last 3 months")
    avg200Days: float | None = Field(default=0.0, description="average volume of last 3 months")


    # updates one time in 3 days
    priceToBook: float | None = Field(default=0.0, description="value of asset")
    enterpriseToEbitda: float | None = Field(default=0.0, description="value of company")
    yearHigh: float | None = Field(default=0.0, description="highest price in current year")
    yearLow: float | None = Field(default=0.0, description="lowest price in current year")
    trailingPE: float | None = Field(default=0.0 , description="trailing pe ratio")
    forwardPE: float | None = Field(default=0.0 , description="forward pe ratio")

    currentRatio: float | None = Field(default=0.0 , description="current ratio of asset")
    debtToEquity: float | None = Field(default=0.0 , description="debt to equity of asset")
    returnOnEquity: float | None = Field(default=0.0 , description="return on equity of asset")
    returnOnAssets: float | None = Field(default=0.0 , description="return on assets")


class StockStats(StatBase, table=True):
    # -- Constant features --
    # -- Dynamic features --
    sector: str | None = Field(default="none")
    summary: str | None = Field(default="none")
    eps: float | None = Field(default=0.0)

    @field_validator(
        "previousClose", "dayHigh", "dayLow", "open", "yearHigh", "yearLow",
        "priceToBook", "enterpriseToEbitda", "trailingPE", "forwardPE",
        "currentRatio", "debtToEquity", "returnOnEquity", "returnOnAssets", "eps",
        mode="before"
    )
    @classmethod
    def round_financial_fields(cls, value: Any) -> float | None:
        """
        rounds 2 digits of given float number after dot
        """
        if value is None:
            return None
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return 0.0