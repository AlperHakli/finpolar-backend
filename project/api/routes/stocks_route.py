from fastapi import APIRouter, Depends , Query
from typing import Union , List
from project.api.repository.stocks_repo import StockRepository
from project.api.base_models import GetSingleStockIndicatorModel , StockStats , CommodityStats
from project.api.dependencies import PostreSqlDbDep , RedisDbDep
from settings import settings
from project.api.base_models import AssetRouteBaseModels
from datetime import datetime

router = APIRouter(prefix="/assets", tags=["Asset Operations"])


# @router.get("/list")
# async def list_stocks():
#     """
#     Fetch all stocks
#     """
#     return await StockRepository.get_all_stocks()


@router.get("/multiple-stocks-filtered-by-sector")
async def multiple_stocks_by_sector(database_session : PostreSqlDbDep):
    """Fetch some number of stocks with given sector"""
    return await StockRepository.get_multiple_stocks_by_sector_list(
        sector_list=settings.SECTOR_LIST,
        database_session=database_session,
        database_model=StockStats,
        limit_per_sector=settings.LIMIT_STOCK_PER_SECTOR
    )

@router.get("/wake-up-server")
async def wake_up_server():
    """only exists to wake up the server"""
    return {"message" : f"Server is awake, time: {datetime.now()}"}
@router.get("/search-asset")
async def search_asset(search_key:str,database_session: PostreSqlDbDep):
    """Fetch search results from service"""
    return await StockRepository.search_asset_service(search_key=search_key , database_session=database_session , database_model=StockStats)
@router.get("/get-top-10-volume-stock-details")
async def get_top_10_volume_stock_details(redis_manager: RedisDbDep , database_session: PostreSqlDbDep):
    """fetch 10 stocks that have most volumes"""
    return await StockRepository.get_top_10_with_details(
        redis_manager=redis_manager,
        database_session=database_session
    )
@router.get("/get-random-10-commodities")
async def get_random_10_commodities(database_session: PostreSqlDbDep):
    """fetch random 10 commodities"""
    return await StockRepository.get_random_10_assets(database_session=database_session , database_model=CommodityStats)

@router.get("/get-random-10-assets-from-all-asset-types")
async def get_random_10_assets_from_all_assets(database_session: PostreSqlDbDep):
    return await StockRepository.get_random_10_assets_from_all_asset_types(database_session=database_session , database_models=settings.ALL_ASSET_MODELS)



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


@router.get("/asset-history")
async def asset_history(
        ticker: str,
        period: str):
    """
    Fetch specified asset history with respect to given period
    :param ticker: str symbol of relevant assets
    :param period: str how long history will be default (1d) available (1d , 5d , 1mo , 2mo , 6mo , 1y , 10y)

    """
    return await StockRepository.get_single_asset_history(ticker=ticker, period=period)
@router.post("/multiple-asset-history")
async def multiple_asset_history(payload: AssetRouteBaseModels.BatchAssetHistoryModel):
    """
    Fetch multiple asset history with given periods and asset symbols
    example payload:
        {
         "requests": [
            {"ticker": "THYAO.IS", "period": "1d"},
            {"ticker": "GC=F", "period": "1mo"}
            ]
        }
    \n



    ticker: symbol of relevant asset
    period: length of history available (1d , 5d , 1mo , 2mo , 6mo , 1y , 10y)
    """
    return await StockRepository.get_multiple_asset_history(payload=payload.requests)



@router.get("/market-indices")
async def get_market_indices(redis_manager: RedisDbDep):
    return await StockRepository.get_market_indices_service(redis_manager=redis_manager)


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