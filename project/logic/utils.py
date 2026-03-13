import polars as pl
from functools import wraps
from project.logic.constants import ALL_TOOLS , ANALYSIS_TOOLS
from project.logic.exceptions import DataTypeException

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
        elif (period == "6mo"):
            return "1d"
        elif (period == "1y"):
            return "1d"
        else:
            return "1wk"
    @staticmethod
    def format_market_cap(n: int):
        """
        Format market cap string
        """
        if n is None: return "N/A"
        for unit in ['', 'K', 'M', 'B', 'T']:
            if abs(n) < 1000.0:
                return f"{n:.2f}{unit}"
            n /= 1000.0
        return f"{n:.2f}T"
    @staticmethod
    def format_symbol(symbol: str):
        """
        Format symbol
        """
        if symbol.endswith(".IS"):
            return symbol[:-3]
        return symbol
    @staticmethod
    def change_percent_calculator(current_close: float, prev_close: float) -> float:
        """
        Calculate change between current price and previous day's close
        """
        change_percent = ((current_close - prev_close) / prev_close) * 100
        return round(change_percent, 2)












