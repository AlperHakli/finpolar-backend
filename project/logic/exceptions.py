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

class SeedFileNotFoundException(FinpolarException):
    "When seeding file does not found fast api throw this"

    def __init__(self , file_path: str):
        self.file_path = file_path
        super().__init__(message=f"CRITICAL ERROR seed data file not found at {file_path}")


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

class DataTypeException(FinpolarException):
    "Throws when data type is not compatible with function"
    def __init__(self , message: str):
        super().__init__(message=message)



