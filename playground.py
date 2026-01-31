import polars
import yfinance
import yfinance as yf
import polars as pl
import pandas as pd


data = yfinance.download("AEFES.IS")

pldata = polars.from_pandas(data)
newdata = pldata.median()
result = f"MEDİAN result of all features: {newdata.row(0 , named=True)}"
print(result)