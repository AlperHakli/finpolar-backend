import asyncio
from typing import Annotated , Any
import yfinance as yf
import polars as pl
import pandas as pd
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from project.ai.agentstate import AgentState
from langgraph.prebuilt import InjectedState

@tool
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
                return (f"Error: No data found for ticker '{ticker}'. "
                        f"Please ensure you have provided the correct stock symbol. ")

            if isinstance(info.columns, pd.MultiIndex):
                info.columns = info.columns.get_level_values(0)

            info.columns = [str(col) for col in info.columns]

            info = info.reset_index()

            info_polars = pl.from_pandas(info)

            return info_polars
        except Exception as e:
            return f"Some error occurded when fetch ticker data: {e}"


@tool
async def calculate_rsi(df: Annotated[Any, InjectedState], period: int = 14):
    """
    Calculate the Relative Strength Index (RSI) using the stock data stored in memory (raw_data).
    """
    try:
        # 1. Veriyi Dönüştürme (Deserialization)
        if isinstance(df, list):
            working_df = pl.from_dicts(df)
        elif isinstance(df, pl.DataFrame):
            working_df = df
        else:
            return "Error: Data format is not supported. Please fetch stock data first."


        close_col = pl.col("Close")
        delta = close_col.diff()


        gain = pl.when(delta > 0).then(delta).otherwise(0.0)
        loss = pl.when(delta < 0).then(delta.abs()).otherwise(0.0)


        avg_gain = gain.rolling_mean(window_size=period)
        avg_loss = loss.rolling_mean(window_size=period)


        rs = avg_gain / avg_loss
        rsi_expr = 100 - (100 / (1 + rs))


        result_df = working_df.with_columns(rsi_expr.alias("RSI"))


        latest_row = result_df.tail(1).to_dicts()[0]

        rsi_value = latest_row["RSI"]
        closing_price = latest_row["Close"]
        ticker = latest_row.get("Ticker", "Unknown")


        if rsi_value is None:
            return "Error: Not enough data to calculate RSI. Please try a shorter period or fetch more data."


        if rsi_value >= 70:
            status = "Overbought (Potential Reversal/Bearish)"
        elif rsi_value <= 30:
            status = "Oversold (Potential Bounce/Bullish)"
        else:
            status = "Neutral"

        return (
            f"Technical Analysis Summary for {ticker}:\n"
            f"- Latest Close: {closing_price:.2f}\n"
            f"- RSI ({period}): {rsi_value:.2f}\n"
            f"- Market Condition: {status}"
        )

    except Exception as e:
        return f"Error during RSI calculation: {str(e)}"


@tool
async def calculate_moving_averages(df: Annotated[Any, InjectedState], short_window: int = 20,
                                    long_window: int = 50):
    """
    Calculate Simple (SMA) and Exponential (EMA) Moving Averages to identify trends.
    Useful for detecting golden crosses or death crosses.
    """
    try:

        working_df = None

        if isinstance(df, list):
            working_df = pl.from_dicts(df)
        elif isinstance(df, pl.DataFrame):
            working_df = df
        else:
            return "Error: Data format is not supported. Please fetch stock data first."



        # Calculate SMAs and EMAs using Polars efficient rolling and EWM methods
        df_ma = working_df.with_columns([
            pl.col("Close").rolling_mean(window_size=short_window).alias(f"SMA_{short_window}"),
            pl.col("Close").rolling_mean(window_size=long_window).alias(f"SMA_{long_window}"),
            pl.col("Close").ewm_mean(span=short_window, adjust=False).alias(f"EMA_{short_window}")
        ])

        latest = df_ma.tail(1).row(0, named=True)

        curr_price = latest["Close"]
        sma_short = latest[f"SMA_{short_window}"]
        sma_long = latest[f"SMA_{long_window}"]

        if sma_short is None or sma_long is None:
            return (f"Moving Average Analysis Error: Not enough data points to calculate TRY TO CALL ANOTHER TOOL"
                    f"SMA_{short_window} or SMA_{long_window}. "
                    f"Required: at least {long_window} days of data.")


        # Determine trend status
        trend = "Bullish Alignment" if sma_short > sma_long else "Bearish Alignment"
        position = "Above SMA" if curr_price > sma_short else "Below SMA"

        return (
            f"Moving Average Analysis:\n"
            f"- Price: {curr_price:.2f}\n"
            f"- SMA {short_window}: {sma_short:.2f}\n"
            f"- SMA {long_window}: {sma_long:.2f}\n"
            f"- Trend Signal: {trend} & {position}"
        )
    except Exception as e:
        return f"Error in Moving Average calculation: {str(e)}"


@tool
async def calculate_bollinger_bands(df: Annotated[Any, InjectedState], period: int = 20, std_dev: int = 2):
    """
    Calculate Bollinger Bands (Upper, Middle, Lower).
    Helps in identifying volatility and potential overbought/oversold levels.
    """
    try:

        working_df = None

        if isinstance(df, list):
            working_df = pl.from_dicts(df)
        elif isinstance(df, pl.DataFrame):
            working_df = df
        else:
            return "Error: Data format is not supported. Please fetch stock data first."



        # Calculate Middle Band (SMA), Standard Deviation, and Upper/Lower Bands
        df_bb = working_df.with_columns([
            pl.col("Close").rolling_mean(window_size=period).alias("Middle_Band"),
            pl.col("Close").rolling_std(window_size=period).alias("Std_Dev")
        ]).with_columns([
            (pl.col("Middle_Band") + (std_dev * pl.col("Std_Dev"))).alias("Upper_Band"),
            (pl.col("Middle_Band") - (std_dev * pl.col("Std_Dev"))).alias("Lower_Band")
        ])

        latest = df_bb.tail(1).row(0, named=True)

        price = latest["Close"]
        upper = latest["Upper_Band"]
        lower = latest["Lower_Band"]

        # Volatility interpretation
        if price >= upper:
            signal = "Price at Upper Band (Potential Overextension)"
        elif price <= lower:
            signal = "Price at Lower Band (Potential Bounce)"
        else:
            signal = "Price within normal volatility range"

        return (
            f"Bollinger Bands Analysis:\n"
            f"- Upper Band: {upper:.2f}\n"
            f"- Middle Band: {latest['Middle_Band']:.2f}\n"
            f"- Lower Band: {lower:.2f}\n"
            f"- Current Position: {signal}"
        )
    except Exception as e:
        return f"Error in Bollinger Bands calculation: {str(e)}"


@tool
async def calculate_macd(df: Annotated[Any, InjectedState], fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculate MACD (Moving Average Convergence Divergence) and Signal Line.
    Used to find momentum shifts and trend reversals.
    """
    try:

        working_df = None

        if isinstance(df, list):
            working_df = pl.from_dicts(df)
        elif isinstance(df, pl.DataFrame):
            working_df = df
        else:
            return "Error: Data format is not supported. Please fetch stock data first."


        # Calculate Fast and Slow EMAs
        df_macd = working_df.with_columns([
            pl.col("Close").ewm_mean(span=fast, adjust=False).alias("EMA_fast"),
            pl.col("Close").ewm_mean(span=slow, adjust=False).alias("EMA_slow")
        ])

        # Calculate MACD Line and Signal Line
        df_macd = df_macd.with_columns(
            (pl.col("EMA_fast") - pl.col("EMA_slow")).alias("MACD_line")
        ).with_columns(
            pl.col("MACD_line").ewm_mean(span=signal, adjust=False).alias("Signal_line")
        )

        latest = df_macd.tail(1).row(0, named=True)

        m_line = latest["MACD_line"]
        s_line = latest["Signal_line"]

        # Determine momentum
        momentum = "Bullish Crossover" if m_line > s_line else "Bearish Crossover"

        return (
            f"MACD Analysis:\n"
            f"- MACD Line: {m_line:.4f}\n"
            f"- Signal Line: {s_line:.4f}\n"
            f"- Momentum Status: {momentum}"
        )
    except Exception as e:
        return f"Error in MACD calculation: {str(e)}"


only_get_stock_tool = [get_stock]
all_tools = [
    get_stock,
    calculate_rsi,
    calculate_moving_averages,
    calculate_bollinger_bands,
    calculate_macd
]
analysis_tools = [
                  "calculate_rsi",
                  "calculate_moving_averages",
                  "calculate_bollinger_bands",
                  "calculate_macd"]
name_to_tool = {tool.name: tool for tool in all_tools}


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


        if tool_name in analysis_tools and temp_raw_data is None:
            async def error_fn():
                return "Error: Data not found in memory. Call 'get_stock' tool first."

            tasks.append(error_fn())
            continue


        if tool_name in analysis_tools:
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
