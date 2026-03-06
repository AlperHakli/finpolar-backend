def interval_calculator(period: str):
    """
    returns appropriate interval with given period
    """
    if(period == "1d"):
        return "5m"
    elif(period == "5d"):
        return "15m"
    elif(period == "1mo"):
        return "1d"
    elif(period == "6mo"):
        return "1d"
    elif(period == "1y"):
        return "1d"
    else:
        return "1wk"



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