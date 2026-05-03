from fastapi import APIRouter , Depends
from project.api.repository.stocks_repo import StockRepository
from project.api.database import get_session
from project.api.base_models import GetSingleStockIndicatorModel
from sqlmodel import Session

router = APIRouter(prefix="/stocks", tags=["Stock Operations"])


# @router.get("/list")
# async def list_stocks():
#     """
#     Fetch all stocks
#     """
#     return await StockRepository.get_all_stocks()


@router.get("/stock-detail")
async def stock_details(ticker: str):
    """
    Fetch specified stock details (except history)
    """
    return await StockRepository.get_single_asset(ticker=ticker)

@router.get("/stock-history")
async def stock_history(ticker: str , period: str):
    """
    Only fetch specified stock history with respect given period
    """
    return await StockRepository.get_single_stock_history(ticker=ticker , period=period)

@router.get("/single-stock-indicators")
async def get_single_stock_indicators(ticker: str , indicator_settings: GetSingleStockIndicatorModel):
    return await StockRepository.get_single_stock_indicators(ticker=ticker , indicator_settings=indicator_settings)

@router.get("/watchlist")
def fetch_watchlist(session: Session = Depends(get_session)):
    """
    Fetch top 10 active , top 10 gainers , top 10 losers
    example output:
    {
    top_volume:top10volume,
    top_gainers:top10gainers,
    top_losers:top10losers
    }
    """
    return StockRepository.get_watchlist(session=session)