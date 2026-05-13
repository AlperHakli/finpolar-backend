import polars as pl
import asyncio
import logging

logger = logging.getLogger(__name__)

class IndicatorService:
    @staticmethod
    async def compute_rsi_logic(df: pl.DataFrame, period: int = 14):
        if len(df) < period:
            return {
            "rsi_value": "NaN",
            "closing_price": "Nan",
            "ticker": "Nan",
            "status": "Nan",
        }
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



    @staticmethod
    async def compute_all_logic(
            df: pl.DataFrame,
            rsi_period: int = 14,  # period for rsi
            bb_period: int = 20,  # period for bollinger
            bb_std_dev: int = 2,  # Bollinger standart deviation
            ma_short: int = 20,  # MA short
            ma_long: int = 50,  # MA long
            macd_fast: int = 12,  # MACD fast
            macd_slow: int = 26,  # MACD slow
            macd_signal: int = 9,  # MACD signal
    ) -> dict:
        """
        Consolidates multiple technical indicators into a single analytical snapshot
        for a given financial security.

        This method aggregates momentum, trend, volatility, and volume-based metrics
        to provide a holistic view of the asset's current market state.

        Args:
            df (pl.DataFrame): Input Polars DataFrame containing OHLCV data.
                Must include 'Close' and 'Volume' columns.
            short_window (int): The period for the short-term Simple Moving Average (SMA)
                and Exponential Moving Average (EMA). Used for immediate trend detection.
            long_window (int): The period for the long-term SMA. Essential for identifying
                macro trend direction and potential 'Golden Cross' or 'Death Cross' events.
            std_dev (int): Number of standard deviations for Bollinger Bands. Defines the
                width of the volatility envelope.
            fast (int): The 'fast' period for MACD EMA calculation (typically 12).
            slow (int): The 'slow' period for MACD EMA calculation (typically 26).
            signal (int): The period for the MACD Signal Line (typically 9).

        Returns:
            dict: A comprehensive dictionary containing:

                --- MOMENTUM (RSI) ---
                - rsi_value: A momentum oscillator (0-100) measuring the speed and change
                  of price movements.
                - status: Qualitative signal based on RSI (Overbought >= 70, Oversold <= 30).

                --- TREND (MA) ---
                - sma_short / sma_long: Baseline trend indicators. Price above SMA
                  suggests an uptrend; price below suggests a downtrend.
                - ema_short: Similar to SMA but prioritizes recent price action,
                  reacting faster to market shifts.

                --- VOLATILITY (Bollinger Bands) ---
                - upper / lower: Volatility boundaries. Prices hitting the upper band
                  may be overextended; hitting the lower band may indicate a value zone.
                - middle: The 20-period SMA acting as a mean-reversion target.

                --- MOMENTUM TREND (MACD) ---
                - m_line: The difference between Fast and Slow EMAs.
                - s_line: The 9-day EMA of the MACD Line. Crossovers between M and S lines
                  are primary buy/sell signals.

                --- INTENSITY (RVOL) ---
                - current_volume: Real-time trading activity.
                - rvol: Ratio of current volume to average volume. RVOL > 2.0 often
                  indicates institutional interest or a potential breakout.
                - price_change: The percentage change between the last two closing prices.
        """
        try:
            tasks = [

                IndicatorService.compute_rsi_logic(df, period=rsi_period),
                IndicatorService.compute_ma_logic(df, short_window=ma_short, long_window=ma_long),
                IndicatorService.compute_bollinger_logic(df, period=bb_period, std_dev=bb_std_dev),
                IndicatorService.compute_macd_logic(df, fast=macd_fast, slow=macd_slow, signal=macd_signal),
                IndicatorService.compute_rvol_logic(df)
            ]

            results = await asyncio.gather(*tasks)

            return {
                "rsi": results[0],
                "moving_averages": results[1],
                "bollinger_bands": results[2],
                "macd": results[3],
                "volume_analysis": results[4]
            }

        except Exception as e:
            logger.error(f"Computation error: {e}")
            return None
