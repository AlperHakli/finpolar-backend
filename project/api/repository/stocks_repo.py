import yfinance
import yfinance as yf


class StockRepository():
    TICKERS = ["AEFES.IS", "THYAO.IS", "AKBNK.IS", "YKBNK.IS"]

    @staticmethod
    async def get_all_stocks():
        """
        Fetch stock informations from yfinance api to fill sidebar
        """
        tickerstring = " ".join(StockRepository.TICKERS)
        data = yfinance.download(tickerstring, period="1d", group_by="ticker")

        summary = []
        for t in StockRepository.TICKERS:
            # last close price
            price = data[t]['Close'].iloc[-1]
            summary.append({
                "ticker": t.replace(".IS", ""),
                "price": round(float(price), 2)
            })
        return summary

    @staticmethod
    async def get_single_stock(ticker: str):
        """
        Fetchs Information about a stock
        """
        if not ticker.endswith(".IS"):
            ticker += ".IS"

        stock = yfinance.Ticker(ticker=ticker)

        info = stock.info
        summary = info.get("longBusinessSummary", "No description available.")
        marketcap = info.get("marketCap")
        symbol = info.get("symbol")

        history = stock.history(period="1mo")["Close"]

        closeData = history.reset_index()

        history = [
            {"date": row["Date"].strftime("%Y-%m-%d"), "price": round(row["Close"], 3)}
            for index, row in closeData.iterrows()
        ]





        short_summary = summary[:520] + "..." if len(summary) > 520 else summary
        short_marketcap = format_market_cap(marketcap)
        formatted_symbol = format_symbol(symbol)
        return {
            "name": info.get("longName"),
            "currentPrice": info.get("currentPrice"),
            "sector": info.get("sector"),
            "marketCap": short_marketcap,
            "peRatio": info.get("trailingPE"),
            "summary": short_summary,
            "symbol": formatted_symbol,
            "history": history,


        }


def format_market_cap(n:int):
    """
    Format market cap string
    """
    if n is None: return "N/A"
    for unit in ['', 'K', 'M', 'B', 'T']:
        if abs(n) < 1000.0:
            return f"{n:.2f}{unit}"
        n /= 1000.0
    return f"{n:.2f}T"

def format_symbol(symbol:str):
    """
    Format symbol
    """
    if symbol.endswith(".IS"): return symbol[:-3]