from fastapi import APIRouter
from project.api.repository.stocks_repo import StockRepository

router = APIRouter(prefix="/stocks", tags=["Stock Operations"])


@router.get("/list")
async def list_stocks():
    return await StockRepository.get_all_stocks()


@router.get("/single-ticker")
async def stock_details(ticker: str):
    return await StockRepository.get_single_stock(ticker=ticker)
