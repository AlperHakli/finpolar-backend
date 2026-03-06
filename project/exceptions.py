class FinpolarException(Exception):
    "Base exception class"
    def __init__(self , message:str):
        self.message = message
        super().__init__(message)

class StockNotFoundException(FinpolarException):
    "Throws when no valid stock found"

    def __init__(self , ticker: str , message: str):
        """
        :param ticker: ticker symbol of relevant stock
        :param message: error message
        """
        self.ticker = ticker
        super().__init__(message=message)
    pass

class YfinanceApiException(FinpolarException):
    "Throws when an error occur from yfinance api"
    def __init__(self , technical_detail: str):
        """
        :param technical_detail: technical error detail for dev
        """
        self.technical_detail = technical_detail

        super().__init__(message="Yfinance service threw an error")
    pass
class ConnectionError(FinpolarException):
    "Throws when connection is disabled"
    pass


