import yfinance
import yfinance as yf


class StockRepository():
    TICKERS = ["AEFES.IS" , "THYAO.IS" , "AKBNK.IS" , "YKBNK.IS"]

    @staticmethod
    async def get_all_stocks():
        """
        Fetch stock informations from yfinance api to fill sidebar
        """
        tickerstring = " ".join(StockRepository.TICKERS)
        data = yfinance.download(tickerstring , period="1d" , group_by="ticker")

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
        stock = yfinance.Ticker(ticker=ticker)

        info = stock.info
        return {
            "name": info.get("longName"),
            "currentPrice": info.get("currentPrice"),
            "sector": info.get("sector"),
            "summary": info.get("longBusinessSummary")[:200] + "..."  # Kısa özet
        }

