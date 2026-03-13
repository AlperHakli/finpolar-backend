import polars as pl


class IndicatorService:
    @staticmethod
    async def compute_rsi_logic(df: pl.DataFrame, period: int = 14):
        close_col = pl.col("Close")
        delta = close_col.diff()
        gain = pl.when(delta > 0).then(delta).otherwise(0.0)
        loss = pl.when(delta < 0).then(delta.abs()).otherwise(0.0)
        avg_gain = gain.rolling_mean(window_size=period)
        avg_loss = loss.rolling_mean(window_size=period)
        rs = avg_gain / avg_loss
        rsi_expr = 100 - (100 / (1 + rs))
        result_df = df.with_columns(rsi_expr.alias("RSI"))
        latest_row = result_df.tail(1).to_dicts()[0]
        val = latest_row["RSI"]
        status = "Overbought (Potential Reversal/Bearish)" if val >= 70 else \
            "Oversold (Potential Bounce/Bullish)" if val <= 30 else "Neutral"

        return {
            "rsi_value": latest_row["RSI"],
            "closing_price": latest_row["Close"],
            "ticker": latest_row.get("Ticker", "Unknown"),
            "status": status,
        }
    @staticmethod
    async def compute_ma_logic(df: pl.DataFrame, short_window: int = 20, long_window: int = 50):
        df_ma = df.with_columns([
            pl.col("Close").rolling_mean(window_size=short_window).alias(f"SMA_{short_window}"),
            pl.col("Close").rolling_mean(window_size=long_window).alias(f"SMA_{long_window}"),
            pl.col("Close").ewm_mean(span=short_window, adjust=False).alias(f"EMA_{short_window}")
        ])
        latest = df_ma.tail(1).row(0, named=True)
        return {
            "curr_price": latest["Close"],
            "sma_short": latest[f"SMA_{short_window}"],
            "sma_long": latest[f"SMA_{long_window}"],
            "short_window": short_window,
            "long_window": long_window
        }
    @staticmethod
    async def compute_bollinger_logic(df: pl.DataFrame, period: int = 20, std_dev: int = 2):
        df_bb = df.with_columns([
            pl.col("Close").rolling_mean(window_size=period).alias("Middle_Band"),
            pl.col("Close").rolling_std(window_size=period).alias("Std_Dev")
        ]).with_columns([
            (pl.col("Middle_Band") + (std_dev * pl.col("Std_Dev"))).alias("Upper_Band"),
            (pl.col("Middle_Band") - (std_dev * pl.col("Std_Dev"))).alias("Lower_Band")
        ])
        latest = df_bb.tail(1).row(0, named=True)
        return {
            "price": latest["Close"],
            "upper": latest["Upper_Band"],
            "lower": latest["Lower_Band"],
            "middle": latest["Middle_Band"]
        }
    @staticmethod
    async def compute_macd_logic(df: pl.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
        df_macd = df.with_columns([
            pl.col("Close").ewm_mean(span=fast, adjust=False).alias("EMA_fast"),
            pl.col("Close").ewm_mean(span=slow, adjust=False).alias("EMA_slow")
        ])
        df_macd = df_macd.with_columns(
            (pl.col("EMA_fast") - pl.col("EMA_slow")).alias("MACD_line")
        ).with_columns(
            pl.col("MACD_line").ewm_mean(span=signal, adjust=False).alias("Signal_line")
        )
        latest = df_macd.tail(1).row(0, named=True)
        return {
            "m_line": latest["MACD_line"],
            "s_line": latest["Signal_line"]
        }
    @staticmethod
    async def compute_rvol_logic(df: pl.DataFrame):
        avg_volume = df["Volume"].mean()
        current_volume = df["Volume"].tail(1)[0]
        last_two_days = df["Close"].tail(2).to_list()
        price_change = ((last_two_days[1] - last_two_days[0]) / last_two_days[0]) * 100
        return {
            "avg_volume": avg_volume,
            "current_volume": current_volume,
            "price_change": price_change,
            "rvol": (current_volume / avg_volume) if avg_volume != 0 else 0
        }

