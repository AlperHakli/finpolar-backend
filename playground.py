import yfinance as yf
from project.logic.utils import change_percent_calculator
def tryfunc(ticker: str):
    ticker = yf.Ticker(ticker="ASELS.IS")
    info = ticker.info

    currentPrice = info.get("currentPrice")
    previousClose = info.get("previousClose")

    print(currentPrice)
    print(previousClose)

    changePercent = change_percent_calculator(current_close=currentPrice, prev_close=previousClose)


    return changePercent


print(tryfunc("THYAO.IS"))

