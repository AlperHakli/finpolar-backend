from fastapi import APIRouter, Depends

from project.api.repository.stocks_repo import StockRepository
from project.api.base_models import GetSingleStockIndicatorModel , StockStats
from project.api.dependencies import PostreSqlDbDep , RedisDbDep
from settings import settings


router = APIRouter(prefix="/stocks", tags=["Stock Operations"])


# @router.get("/list")
# async def list_stocks():
#     """
#     Fetch all stocks
#     """
#     return await StockRepository.get_all_stocks()


@router.get("/stock-detail")
async def stock_details(
        ticker: str,
        database_session : PostreSqlDbDep,
        redis_manager: RedisDbDep


):
    """
    Fetch specified stock details from database and redis (except history)

    :param ticker: symbol of asset
    :param database_session: current database session
    :param redis_manager: redis manager obj
    """

    return await StockRepository.get_single_asset_information_master(
        symbol=ticker,
        database_session=database_session,
        database_model=StockStats,
        redis_manager=redis_manager,
        redis_stats=settings.GET_SINGLE_ASSET_REALTIME_DATA_STATS

    )


@router.get("/stock-history")
async def stock_history(ticker: str , period: str):
    """
    Only fetch specified stock history with respect given period
    """
    return await StockRepository.get_single_asset_history(ticker=ticker, period=period)

@router.post("/single-stock-indicators")
async def get_single_stock_indicators(
        redis_manager: RedisDbDep,
        indicator_settings: GetSingleStockIndicatorModel
):
    return await StockRepository.get_single_stock_indicators(
        indicator_settings=indicator_settings,
        redis_manager=redis_manager,
 )

@router.get("/watchlist")
async def fetch_watchlist(redis_manager: RedisDbDep):
    """
    Fetch top 10 active , top 10 gainers , top 10 losers
    example output:
    {
    top_volume:top10volume,
    top_gainers:top10gainers,
    top_losers:top10losers
    }
    """
    return await StockRepository.get_watchlist(redis_manager=redis_manager)