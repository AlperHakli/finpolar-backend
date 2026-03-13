import asyncio
from typing import Annotated, Any
import yfinance as yf
import polars as pl
import pandas as pd
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from project.ai.data_models import AgentState
from langgraph.prebuilt import InjectedState
from project.logic.exceptions import StockNotFoundException
from project.logic.utils import ToolWrapper
from project.logic.constants import ALL_TOOLS , ANALYSIS_TOOLS
from project.logic.indicator_service import IndicatorService


@ToolWrapper.register_tool()
@tool()
async def get_stock(ticker: str) -> pl.DataFrame | str:
    """
    :param ticker : ticker of specified stock
    Use it to get data from specified stock
    """
    ticker.upper()
    if not (ticker.endswith(".IS")):
        ticker += ".IS"

        try:
            info = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True)

            if info is None or info.empty:
                raise StockNotFoundException(
                    message="No data found for specified ticker",
                    ticker=ticker
                )

            if isinstance(info.columns, pd.MultiIndex):
                info.columns = info.columns.get_level_values(0)

            info.columns = [str(col) for col in info.columns]

            info = info.reset_index()

            info_polars = pl.from_pandas(info)

            return info_polars

        except StockNotFoundException as s:
            raise s

        except Exception as e:
            return f"Some error occurded when fetch ticker data: {e}"

@ToolWrapper.register_tool(category="analysis")
@tool
@ToolWrapper.data_deserialization
async def calculate_rsi(df: Annotated[Any, InjectedState], period: int = 14):
    """Calculate the Relative Strength Index (RSI)."""
    try:
        data = await IndicatorService.compute_rsi_logic(df, period)
        val, price, ticker , status = data["rsi_value"], data["closing_price"], data["ticker"] , data["status"]

        if val is None: return "Error: Not enough data to calculate RSI."


        return (f"Technical Analysis Summary for {ticker}:\n"
                f"- Latest Close: {price:.2f}\n"
                f"- RSI ({period}): {val:.2f}\n"
                f"- Market Condition: {status}")
    except Exception as e:
        return f"Error during RSI calculation: {str(e)}"


@ToolWrapper.register_tool(category="analysis")
@tool
@ToolWrapper.data_deserialization
async def calculate_moving_averages(df: Annotated[Any, InjectedState], short_window: int = 20, long_window: int = 50):
    """Calculate SMA and EMA trends."""
    try:
        data = await IndicatorService.compute_ma_logic(df, short_window, long_window)
        p, s_s, s_l = data["curr_price"], data["sma_short"], data["sma_long"]

        if s_s is None or s_l is None:
            return f"Moving Average Analysis Error: Not enough data points..."

        trend = "Bullish Alignment" if s_s > s_l else "Bearish Alignment"
        pos = "Above SMA" if p > s_s else "Below SMA"

        return (f"Moving Average Analysis:\n"
                f"- Price: {p:.2f}\n"
                f"- SMA {short_window}: {s_s:.2f}\n"
                f"- SMA {long_window}: {s_l:.2f}\n"
                f"- Trend Signal: {trend} & {pos}")
    except Exception as e:
        return f"Error in Moving Average: {str(e)}"


@ToolWrapper.register_tool(category="analysis")
@tool
@ToolWrapper.data_deserialization
async def calculate_bollinger_bands(df: Annotated[Any, InjectedState], period: int = 20, std_dev: int = 2):
    """Calculate Bollinger Bands."""
    try:
        data = await IndicatorService.compute_bollinger_logic(df, period, std_dev)
        p, u, l, m = data["price"], data["upper"], data["lower"], data["middle"]

        signal = "Price at Upper Band (Potential Overextension)" if p >= u else \
            "Price at Lower Band (Potential Bounce)" if p <= l else \
                "Price within normal volatility range"

        return (f"Bollinger Bands Analysis:\n"
                f"- Upper Band: {u:.2f}\n"
                f"- Middle Band: {m:.2f}\n"
                f"- Lower Band: {l:.2f}\n"
                f"- Current Position: {signal}")
    except Exception as e:
        return f"Error in Bollinger: {str(e)}"


@ToolWrapper.register_tool(category="analysis")
@tool
@ToolWrapper.data_deserialization
async def calculate_macd(df: Annotated[Any, InjectedState], fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD and Signal Line."""
    try:
        data = await IndicatorService.compute_macd_logic(df, fast, slow, signal)
        m, s = data["m_line"], data["s_line"]
        mom = "Bullish Crossover" if m > s else "Bearish Crossover"

        return (f"MACD Analysis:\n"
                f"- MACD Line: {m:.4f}\n"
                f"- Signal Line: {s:.4f}\n"
                f"- Momentum Status: {mom}")
    except Exception as e:
        return f"Error in MACD: {str(e)}"


@ToolWrapper.register_tool(category="analysis")
@tool
@ToolWrapper.data_deserialization
async def calculate_relative_volume(df: Annotated[Any, InjectedState]):
    """Calculate Relative Volume (RVOL)."""
    try:
        data = await IndicatorService.compute_rvol_logic(df)
        if data["avg_volume"] == 0: return "Volume Analysis Error: Average volume is zero."

        r, cv, av, pc = data["rvol"], data["current_volume"], data["avg_volume"], data["price_change"]

        status = "Extreme Volume Spike (High Interest)" if r >= 2.0 else \
            "Significant Volume Increase" if r >= 1.5 else \
                "Low Relative Volume (Dormant)" if r < 0.5 else "Normal"

        sig = "Bullish Confirmation (Accumulation)" if r > 1.2 and pc > 1 else \
            "Bearish Confirmation (Distribution/Panic)" if r > 1.2 and pc < -1 else "Neutral"

        return (f"Volume Analysis (RVOL):\n"
                f"- Current Volume: {cv:,.0f}\n"
                f"- 150D Avg Volume: {av:,.0f}\n"
                f"- RVOL Ratio: {r:.2f}\n"
                f"- Activity Status: {status}\n"
                f"- Price-Volume Signal: {sig} ({pc:.2f}% price change)")
    except Exception as e:
        return f"Error in Volume: {str(e)}"



name_to_tool = {tool.name: tool for tool in ALL_TOOLS}


async def custom_tool_executor(state: AgentState):
    last_message = state.get("messages")[-1]
    tool_calls = last_message.tool_calls
    temp_raw_data = state.get("raw_data")

    if isinstance(temp_raw_data, str):
        temp_raw_data = None

    tool_messages = []
    tasks = []

    has_get_stock = any(call["name"] == "get_stock" for call in tool_calls)

    for call in tool_calls:
        tool_name = call["name"]
        args = call["args"].copy()

        if has_get_stock and tool_name != "get_stock":
            async def skip_fn():
                return "Analysis skipped because new data is being fetched. Please retry after data update."

            tasks.append(skip_fn())
            continue

        toolfn = name_to_tool[tool_name]

        if tool_name == "get_stock":
            tasks.append(toolfn.ainvoke(args))
            continue

        if tool_name in ANALYSIS_TOOLS and temp_raw_data is None:
            async def error_fn():
                return "Error: Data not found in memory. Call 'get_stock' tool first."

            tasks.append(error_fn())
            continue

        if tool_name in ANALYSIS_TOOLS:
            args["df"] = temp_raw_data
            tasks.append(toolfn.ainvoke(args))
        else:

            tasks.append(toolfn.ainvoke(args))

    observations = await asyncio.gather(*tasks)

    for call, obs in zip(tool_calls, observations):
        content = str(obs)

        if call["name"] == "get_stock":

            is_dataframe = hasattr(obs, "columns")

            if is_dataframe:
                temp_raw_data = obs
                content = "raw stock data successfully updated"
            else:
                # Hata durumunda state'i bozma
                content = f"Tool Error: The ticker '{call['args']['ticker']}' returned no data. Ask the user for the correct symbol."

        tool_messages.append(ToolMessage(
            content=content,
            tool_call_id=call["id"]
        ))

    serializable_raw_data = temp_raw_data
    if hasattr(temp_raw_data, "to_dicts"):  # Polars check
        serializable_raw_data = temp_raw_data.to_dicts()
    elif hasattr(temp_raw_data, "to_dict"):  # Pandas check
        serializable_raw_data = temp_raw_data.to_dict(orient="records")

    return {"messages": tool_messages, "raw_data": serializable_raw_data}
