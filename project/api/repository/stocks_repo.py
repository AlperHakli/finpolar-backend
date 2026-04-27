import json
import os

import yfinance
import logging

import polars as pl
import pandas as pd
from sqlmodel import Session , select
from project.logic.exceptions import StockNotFoundException, YfinanceApiException
from project.logic.utils import IndicatorCalculationUtils
from project.api.base_models import TopVolumeStocksModel , MasterTicker , GetSingleStockIndicatorModel
from project.logic.indicator_service import IndicatorService
from project.api.redis_client import redis_manager
from project.api.database import engine
from project.api.repository.analysis_repo import S



logger = logging.getLogger(__name__)


class StockRepository():
    @staticmethod
    async def get_single_stock(ticker: str):
        """
        Fetch Information about a stock (except history)
        """
        try:

            # Works only for turkish stocks I will update this to work all stocks
            if not ticker.endswith(".IS"):
                ticker += ".IS"

            stock = yfinance.Ticker(ticker=ticker)

            info = stock.info

            if not info or info.get("currentPrice") is None:
                raise StockNotFoundException(
                    ticker=ticker,
                    message="Error in get_single_stock invalid stock name or no data found for relevant stock")

            name = info.get("longName")
            currentPrice = info.get("currentPrice")
            previousClose = info.get("previousClose")
            sector = info.get("sector")
            marketcap = info.get("marketCap")
            peRatio = info.get("trailingPE")
            summary = info.get("longBusinessSummary", "No description available.")
            symbol = info.get("symbol")

            changePercent = IndicatorCalculationUtils.change_percent_calculator(current_close=currentPrice, prev_close=previousClose)
            short_summary = summary[:520] + "..." if len(summary) > 520 else summary
            short_marketcap = IndicatorCalculationUtils.format_market_cap(marketcap)
            formatted_symbol = IndicatorCalculationUtils.format_symbol(symbol)
            changeDigit_raw = currentPrice - previousClose
            changeDigit = f"{changeDigit_raw:.2f}"
            currentPrice_edited = f"{currentPrice:.2f}"

            return {
                "name": name,
                "currentPrice": currentPrice_edited,
                "previousClose": previousClose,
                "changePercent": changePercent,
                "changeDigit" : changeDigit,
                "sector": sector,
                "marketCap": short_marketcap,
                "peRatio": peRatio,
                "summary": short_summary,
                "symbol": formatted_symbol,
            }
        except StockNotFoundException:
            logger.warning(f"Invalid or missing ticker when get_single_stock : {ticker}")
            raise
        except Exception as e:
            logger.error(f"Error when get_single_stock {ticker} detail: {e}")
            raise YfinanceApiException(technical_detail=str(e))

    @staticmethod
    async def get_single_stock_history(ticker: str, period: str):
        """
        Fetch only history data of stock
        :param ticker: symbol of relevant stock
        :param period: period (1mo , 1h , 1y etc.)
        :return: stock history with respect to given period
        """
        try:

            df = await StockRepository._fetch_raw_stock_df(ticker=ticker , period=period)

            time_col = "Date" if "Date" in df.columns else "Datetime"

            history = df.select(
                [
                    pl.col(time_col).dt.strftime("%Y-%m-%d" if time_col == "Date" else "%Y-%m-%d %H:%M").alias("date"),
                    pl.col("Close").round(3).alias("price")
                ]
            ).to_dicts()

            return {"history": history}

        except StockNotFoundException:
            logger.warning(f"Invalid or missing ticker when get_single_stock : {ticker}")
            raise
        except Exception as e:
            logger.error(f"Error when get_single_stock_history {ticker}")
            raise YfinanceApiException(technical_detail=str(e))

    @staticmethod
    async def _fetch_raw_stock_df(ticker: str, period: str):
        """
        Fetch data from yfinance returns raw polars dataframe
        """
        if not ticker.endswith(".IS"):
            ticker += ".IS"

        interval = IndicatorCalculationUtils.interval_calculator(period=period)
        stock = yfinance.Ticker(ticker=ticker)
        df_pd = stock.history(period=period, interval=interval)

        if df_pd.empty:
            raise StockNotFoundException(ticker=ticker, message="History not found")

        # convert to polars from pandas and convert index(date) to column
        return pl.from_pandas(df_pd.reset_index())

    @staticmethod
    def get_watchlist(session: Session):
        try:

            return session.exec(select(TopVolumeStocksModel)).all()

        except Exception as e:
            logger.error(f"An error occurded: {e}")
            raise e

    @staticmethod
    def update_top_volume_stocks():
        try:
            all_symbols_global = []
            logger.info("update top 10 volume stocks initialized")
            with Session(engine) as session:
                old_stocks = session.exec(select(TopVolumeStocksModel))
                for old_stock in old_stocks:
                    session.delete(old_stock)
                session.commit()
                logger.info("old top 10 volume stocks successfully deleted")
                all_symbols_global = session.exec(select(MasterTicker.symbol)).all()

            if not all_symbols_global:
                raise Exception("MasterTicker is empty or all symbols is empty")
            data = yfinance.download(all_symbols_global, period="2d", group_by="ticker")
            if data.empty:
                logger.error("Yfinance couldn't downloaded any data maybe stock market is not available")

            volume_list = []

            for ticker in all_symbols_global:
                stock = data[ticker]
                if not stock.empty and len(stock) >= 0:
                    volume = stock["Volume"].iloc[-1]
                    current_close = stock["Close"].iloc[-1]
                    prev_close = stock["Close"].iloc[-2]

                    if pd.isna(volume) or pd.isna(current_close) or volume <= 0:
                        continue

                    trade_value = volume * current_close

                    change_percent = IndicatorCalculationUtils.change_percent_calculator(current_close=current_close, prev_close=prev_close)

                    volume_list.append(
                        {
                            "symbol": ticker.replace(".IS", ""),
                            "price": round(float(current_close), 2),
                            "trade_value": float(trade_value),
                            "changePercent": round(float(change_percent), 2),
                        }
                    )

            top_10_stocks = sorted(volume_list, key=lambda x: x["trade_value"], reverse=True)[:10]

            with Session(engine) as session:
                for stock in top_10_stocks:
                    single_row = TopVolumeStocksModel(symbol=stock.get("symbol"), price=stock.get("price"), trade_value=stock.get("trade_value") , changePercent = stock.get("changePercent"))
                    session.add(single_row)
                session.commit()
            logger.info("Top 10 volume stocks updated")
        except Exception as e:
            logger.error(f"An error occurded {e}")
            raise e



    @staticmethod
    async def get_single_stock_indicators(ticker: str , indicator_settings: GetSingleStockIndicatorModel):
        cached_val = redis_manager.getIndicatorDict(name=ticker)
        if cached_val:
            return cached_val

        df = await StockRepository._fetch_raw_stock_df(ticker=ticker, period="1mo")

        calculated_indicators = IndicatorService.compute_all_logic(df=df,**indicator_settings.model_dump())

        #TODO redis e yazma işini hallet exception ekle bu kısmı bitir sonra en çok artan hisseleride döndüren backendi yaz




