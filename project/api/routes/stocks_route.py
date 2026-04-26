from fastapi import APIRouter
from project.api.repository.stocks_repo import StockRepository

router = APIRouter(prefix="/stocks", tags=["Stock Operations"])


@router.get("/list")
async def list_stocks():
    """
    Fetch all stocks
    """
    return await StockRepository.get_all_stocks()


@router.get("/stock-detail")
async def stock_details(ticker: str):
    """
    Fetch specified stock details (except history)
    """
    return await StockRepository.get_single_stock(ticker=ticker)

@router.get("/stock-history")
async def stock_history(ticker: str , period: str):
    """
    Only fetch specified stock history with respect given period
    """
    return await StockRepository.get_single_stock_history(ticker=ticker , period=period)

@router.get("/watchlist")
def fetch_watchlist():
    """
    Fetch top 10 active stocks
    """

    return StockRepository.get_watchlist()