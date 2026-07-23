import random

import polars as pl
from pandas import DataFrame
from datetime import datetime
import logging
from functools import wraps

import yfinance

from project.ai.constants import ALL_TOOLS, ANALYSIS_TOOLS
from project.logic.exceptions import DataTypeException
from settings import settings

logger = logging.getLogger(__name__)


class ToolWrapper:
    @staticmethod
    def data_deserialization(func):
        """
        Data deserialization wrapper for chat tools
        It converts list to pl.DataFrame
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            df = kwargs.get("df")

            if isinstance(df, list):
                kwargs["df"] = pl.from_dicts(df)
            elif isinstance(df, pl.DataFrame):
                pass
            else:
                raise DataTypeException(
                    message=f"Expected list or polars.DataFrame got {type(df)}"
                )

            return await func(*args, **kwargs)

        return wrapper

    @staticmethod
    def register_tool(category: str = "general"):
        """
        Append tool name and tool object automatically to ANALYSIS_TOOLS list and ALL_TOOLS list that inside project.constants.py
        """

        def decorator(tool_obj):
            if tool_obj not in ALL_TOOLS:
                ALL_TOOLS.append(tool_obj)

                if category == "analysis":

                    name = getattr(tool_obj, "name")
                    if name not in ANALYSIS_TOOLS:
                        ANALYSIS_TOOLS.append(name)
            return tool_obj

        return decorator


class IndicatorCalculationUtils:
    @staticmethod
    def interval_calculator(period: str):
        """
        returns appropriate interval with given period
        """
        if (period == "1d"):
            return "5m"
        elif (period == "5d"):
            return "15m"
        elif (period == "1mo"):
            return "1d"
        elif (period == "2mo"):
            return "1d"
        elif (period == "6mo"):
            return "1d"
        elif (period == "1y"):
            return "1d"
        else:
            return "1wk"

    # @staticmethod
    # def format_market_cap(n: int):
    #     """
    #     Format market cap string
    #     """
    #     if n is None: return "N/A"
    #     for unit in ['', 'K', 'M', 'B', 'T']:
    #         if abs(n) < 1000.0:
    #             return f"{n:.2f}{unit}"
    #         n /= 1000.0
    #     return f"{n:.2f}T"

    # @staticmethod
    # def format_symbol(symbol: str):
    #     """
    #     Format symbol
    #     """
    #     if symbol.endswith(".IS"):
    #         return symbol[:-3]
    #     return symbol
    @staticmethod
    def change_percent_calculator(current_close: float, prev_close: float) -> float:
        """
        Calculate change between current price and previous day's close
        """
        change_percent = ((current_close - prev_close) / prev_close) * 100
        return round(change_percent, 2)

    @staticmethod
    def work_time_controller() \
            -> bool:
        """
        Controls if stock market is open or not
        True = Open , False Closed
        """
        now = datetime.now()
        # is weekend
        if now.weekday() >= 5:
            logger.info("Stock market is not available (weekend) skipping update...")
            return False

        # Out of work times?
        current_time = now.strftime("%H:%M")
        if not ("09:40" <= current_time <= "18:15"):
            logger.info("Stock market is not available (Out of work hours) skipping update...")
            return False

        return True

    @staticmethod
    def add_random_seconds_to_sleep_time_between_chunks(sleep_time: float) -> float:
        """
        as it says , it adds random seconds to given variable
        """
        randomvariable = random.uniform(0.3, 1.2)
        return sleep_time + randomvariable
    @staticmethod
    def format_summary_length(summary_length: int, summary: str):
        """
        Format summary length if given max summary character length greater than length of summary returns summary
        :return: first "." character of summary with greater character length than given summary length digit
        """

        if (len(summary) > summary_length):

            sum_first_half = summary[:summary_length]
            sum_second_half = summary[summary_length:]

            summary_temp = ""
            for c in sum_second_half:
                summary_temp += c
                if c == ".":
                    break

            return sum_first_half + summary_temp

        else:
            return summary

    # -- Formatter Orchestrator --

    FORMATTERS = {
        # "marketCap": lambda val: IndicatorCalculationUtils.format_market_cap(val),
        "summary": lambda val: IndicatorCalculationUtils.format_summary_length(
            summary=val,
            summary_length=settings.MAX_SUMMARY_LENGTH
        ),
        # "symbol": lambda val: IndicatorCalculationUtils.format_symbol(val),
        "previousClose": lambda val: round(float(val), 2) if val else 0.0,

    }

    @staticmethod
    def format_orchestrator(data: dict) -> dict:
        """
        Applies format rule for every key that in data
        """
        formatted_data = {}

        for key, value in data.items():
            #if a formatter exists for given stat then use it otherwise use raw data
            formatter = IndicatorCalculationUtils.FORMATTERS.get(key)
            if formatter and value is not None:
                formatted_data[key] = formatter(value)
            else:
                formatted_data[key] = value

        return formatted_data
    #TODO refactor this formatter


class HelperFunctions():
    @staticmethod
    def fetch_1d_history(inner_chunk: list[str]) -> DataFrame:
        inner_data = yfinance.download(inner_chunk, period="1d", group_by="ticker", progress=False)
        return inner_data

    @staticmethod
    def fetch_history(symbol: str, period: str, interval: str) -> DataFrame:
        """
        fetch history of given symbol with respect to period and interval
        """
        asset = yfinance.Ticker(ticker=symbol)
        df_pd = asset.history(period=period, interval=interval)
        return df_pd
