import json
import os

import yfinance
import logging
from project.logic.exceptions import StockNotFoundException, YfinanceApiException
import polars as pl
import pandas as pd
from project.logic.utils import IndicatorCalculationUtils


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

            return {
                "name": name,
                "currentPrice": currentPrice,
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
        interval = IndicatorCalculationUtils.interval_calculator(period=period)

        if not ticker.endswith(".IS"):
            ticker += ".IS"

        stock = yfinance.Ticker(ticker=ticker)

        df_pd = stock.history(period=period, interval=interval)

        if df_pd.empty:
            raise StockNotFoundException(ticker=ticker, message=f"There is no history with given ticker")

        df = pl.from_pandas(df_pd.reset_index())

        time_col = "Date" if "Date" in df.columns else "Datetime"

        history = df.select([
            pl.col(time_col).dt.strftime("%Y-%m-%d" if time_col == "Date" else "%Y-%m-%d %H:%M").alias("date"),
            pl.col("Close").round(3).alias("price")
        ]).to_dicts()

        return {"history": history}

        # try:

        # except StockNotFoundException:
        #     logger.warning(f"Invalid or missing ticker when get_single_stock : {ticker}")
        #     raise
        # except Exception as e:
        #     logger.error(f"Error when get_single_stock_history {ticker}")
        #     raise YfinanceApiException(technical_detail=str(e))

    @staticmethod
    async def get_watchlist():

        current_dir = os.path.dirname(os.path.abspath(__file__))

        file_path = os.path.join(current_dir, "top_volume.json")

        logger.info(f"Trying to open: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            return {"message": "Try again after 18.15 "}

    @staticmethod
    def update_top_volume_stocks():

        current_dir = os.path.dirname(os.path.abspath(__file__))

        file_path = os.path.join(current_dir, "bist_tickers.json")

        logger.info(f"Trying to open: {file_path}")

        with open(file_path, "r") as f:
            all_tickers = json.load(f)["bist_tickers"]

        data = yfinance.download(all_tickers, period="2d", group_by="ticker")

        volume_list = []

        for ticker in all_tickers:
            stock = data[ticker]
            if not stock.empty and len(stock) >= 2:
                volume = stock["Volume"].iloc[-1]
                current_close = stock["Close"].iloc[-1]
                prev_close = stock["Close"].iloc[-2]

                if pd.isna(volume) or pd.isna(current_close) or volume <= 0:
                    continue

                trade_value = volume * current_close

                change_percent = IndicatorCalculationUtils.change_percent_calculator(current_close=current_close, prev_close=prev_close)

                volume_list.append({
                    "symbol": ticker.replace(".IS", ""),
                    "price": round(float(current_close), 2),
                    "trade_value": float(trade_value),
                    "changePercent": round(float(change_percent), 2),
                })

        top_10_stocks = sorted(volume_list, key=lambda x: x["trade_value"], reverse=True)[:10]
        output_path = os.path.join(current_dir, "top_volume.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(top_10_stocks, f, indent=2)
            logger.info("Daily top volume stock update completed")


    @staticmethod
    async def get_multiple_indicators():
        ...
        #TODO complete here

