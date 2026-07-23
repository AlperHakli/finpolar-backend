from dotenv import load_dotenv
import os
from pathlib import Path
from project.api.base_models import StockStats, CommodityStats


load_dotenv()




class Settings():
    DATABASE_URL = os.getenv("POSTRESQL_DATABASE_URL")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_HOST = os.getenv("REDIS_HOST")

    # DATABASE_URL = os.getenv("LOCALHOST_POSTRESQL_DATABASE_URL")
    # REDIS_PORT = os.getenv("REDIS_PORT")
    # REDIS_HOST = os.getenv("LOCAL_REDIS_HOST")

    # production mode if true the program doesn't update current postresql at first initialization only update redis
    PRODUCTION_MODE = False

    # database seeding settings base path of all datas is data folder
    # example: {"table_model1":"json_file_name1" , "table_model2" : "json_file_name2"}
    # table models must inherit from sqlmodel.SQLModel
    # example json file: {"asset_symbol1" : "asset_name1" , "asset_symbol2": "asset_name2"}
    DATABASE_SEEDING_SETTINGS = {
        StockStats: "stock_seed_database.json",
        CommodityStats: "commodity_seed_database.json",
    }
    ASSET_NAME_TO_TABLE_MODEL_SETTINGS = {
        "stock" : StockStats,
        "commodity": CommodityStats
    }
    TABLE_MODEL_NAME_TO_ASSET_NAME_SETINGS = {
        StockStats: "stock",
        CommodityStats: "commodity"
    }
    ALL_ASSET_MODELS = [StockStats , CommodityStats]

    #base project path
    BASE_DIR: Path = Path(__file__).resolve().parent
    #base seeding part
    DATA_DIR: Path = BASE_DIR / "data"

    STOCK_SEED_FILEPATH: Path = DATA_DIR / "stock_seed_database.json"

    #chunk size for daily update function
    DAILY_UPDATE_CHUNK_SIZE: int = 20
    #sleep time (seconds) between chunks for daily update function
    DAILY_UPDATE_SLEEP_TIME: int = 1
    #time between jobs (days) for daily update function
    DAILY_UPDATE_TIME_BETWEEN_JOBS: int = 1

    #chunk size for realtime update function
    REALTIME_UPDATE_CHUNK_SIZE: int = 50
    #sleep time (seconds) between chunks for realtime update function
    REALTIME_UPDATE_SLEEP_TIME: int = 0.5
    #time between jobs (minutes) for realtime update function
    REALTIME_UPDATE_TIME_BETWEEN_JOBS: int = 240

    #chunk size for longtime update function
    LONGTIME_UPDATE_CHUNK_SIZE: int = 50
    #sleep time (seconds) between chunks for longtime update function
    LONGTIME_UPDATE_SLEEP_TIME: int = 5
    #time between jobs (days) for longtime update function
    LONGTIME_UPDATE_TIME_BETWEEN_JOBS: int = 3

    #chunk size for very longtime update function
    VERY_LONG_TIME_CHUNK_SIZE: int = 50
    #sleep time (seconds) between chunks for very longtime update function
    VERY_LONGTIME_UPDATE_SLEEP_TIME: int = 10
    #time between jobs (days) for very longtime update function
    VERY_LONGTIME_UPDATE_TIME_BETWEEN_JOBS: int = 7

    # -- Update stats --

    """
    example stats:
    {
    "name_of_table_column":"name_of_yfinance.info_or_yfinance.fast_info_attribute"
    }
    """

    STOCK_VERY_LONGTIME_UPDATE_STATS = {
        "eps": "trailingEps",
        "sector": "sector",
        "summary": "longBusinessSummary",
        "symbol": "symbol"

    }

    STOCK_DAILY_UPDATE_STATS = {

        "previousClose": "previous_close",
        "dayHigh": "day_high",
        "dayLow": "day_low",
        "volume": "last_volume",
        "open": "open",
        "marketCap": "market_cap",
        "yearHigh": "year_high",
        "yearLow": "year_low",

        "avgVolume10Days": "ten_day_average_volume",
        "avgVolume3Months": "three_month_average_volume",
        "avg50Days": "fifty_day_average",
        "avg200Days": "two_hundred_day_average",
        "lastVolume": "last_volume"
    }

    STOCK_LONGTIME_UPDATE_STATS = {
        "forwardPE": "forwardPE",
        "priceToBook": "priceToBook",
        "enterpriseToEbitda": "enterpriseToEbitda",
        "currentRatio": "currentRatio",
        "debtToEquity": "debtToEquity",
        "returnOnEquity": "returnOnEquity",
        "returnOnAssets": "returnOnAssets",
    }

    COMMODITY_DAILY_UPDATE_STATS = {
        "open": "regularMarketPrice",
        "previousClose": "regularMarketPreviousClose",
        "dayHigh": "regularMarketDayHigh",
        "dayLow": "regularMarketDayLow"
    }
    COMMODITY_LONGTIME_UPDATE_STATS = {
        "marketCap": "openInterest",
        "volume": "volume",
        "lastVolume": "regularMarketVolume"
    }
    COMMODITY_VERY_LONGTIME_UPDATE_STATS = {
        "yearHigh": "fiftyTwoWeekHigh",
        "yearLow": "fiftyTwoWeekLow",
        "avg50Days": "fiftyDayAverage"
    }

    """
    example stats:
    ["name_of_stat_in_yfinance_fastinfo"]
    """
    GET_SINGLE_ASSET_REALTIME_DATA_STATS = ["last_price"]

    #indicates name of a job using when logging

    DAILY_UPDATE_JOBNAME = "daily-update-job"
    LONGTIME_UPDATE_JOBNAME = "longtime-update-job"
    VERY_LONGTIME_UPDATE_JOBNAME = "very-longtime-update-job"

    #max length of summary (character)
    MAX_SUMMARY_LENGTH = 1500

    #number of stocks that fetch with given sector
    STOCK_NUMBER_FETCH_WITH_GIVEN_SECTOR = 10

    # period of main menu initial stock history default (1d) available (1d , 5d , 1mo , 2mo , 6mo , 1y , 10y)
    MAIN_MENU_ASSET_GRAPH_PERIOD = "1d"

    STOCK_UPDATE_INTERVALS = {
        "daily_update" : DAILY_UPDATE_TIME_BETWEEN_JOBS,
        "once_in_three_days_stats": LONGTIME_UPDATE_TIME_BETWEEN_JOBS,
        "weekly_update": VERY_LONGTIME_UPDATE_TIME_BETWEEN_JOBS,
    }

    # =====================================================================
    # MAIN SETTINGS DICTIONARY
    # =====================================================================
    stock_update_jobs_config = {

        # daily update
        "daily_update": {
            "stock": {
                "stats": STOCK_DAILY_UPDATE_STATS,
                "jobtype": f"stock_{DAILY_UPDATE_JOBNAME}",
                "chunk_size": DAILY_UPDATE_CHUNK_SIZE,
                "sleep_time": DAILY_UPDATE_SLEEP_TIME,
                "use_fast_info": True
            },
            "commodity": {
                "stats": COMMODITY_DAILY_UPDATE_STATS,
                "jobtype": f"commodity_{DAILY_UPDATE_JOBNAME}",
                "chunk_size": DAILY_UPDATE_CHUNK_SIZE,
                "sleep_time": DAILY_UPDATE_SLEEP_TIME,
                "use_fast_info": False
            }
        },

        # once in three days update
        "once_in_three_days_stats": {
            "stock": {
                "stats": STOCK_LONGTIME_UPDATE_STATS,
                "jobtype": f"stock_{LONGTIME_UPDATE_JOBNAME}",
                "chunk_size": LONGTIME_UPDATE_CHUNK_SIZE,
                "sleep_time": LONGTIME_UPDATE_SLEEP_TIME,
                "use_fast_info": False
            },
            "commodity": {
                "stats": COMMODITY_LONGTIME_UPDATE_STATS,
                "jobtype": f"commodity_{LONGTIME_UPDATE_JOBNAME}",
                "chunk_size": LONGTIME_UPDATE_CHUNK_SIZE,
                "sleep_time": LONGTIME_UPDATE_SLEEP_TIME,
                "use_fast_info": False
            }
        },

        # weekly update
        "weekly_update": {
            "stock": {
                "stats": STOCK_VERY_LONGTIME_UPDATE_STATS,
                "jobtype": f"stock_{VERY_LONGTIME_UPDATE_JOBNAME}",
                "chunk_size": VERY_LONG_TIME_CHUNK_SIZE,
                "sleep_time": VERY_LONGTIME_UPDATE_SLEEP_TIME,
                "use_fast_info": False
            },
            "commodity": {
                "stats": COMMODITY_VERY_LONGTIME_UPDATE_STATS,
                "jobtype": f"commodity_{VERY_LONGTIME_UPDATE_JOBNAME}",
                "chunk_size": VERY_LONG_TIME_CHUNK_SIZE,
                "sleep_time": VERY_LONGTIME_UPDATE_SLEEP_TIME,
                "use_fast_info": False
            }
        }
    }



    # AI summary redis duration(seconds)
    AI_SUMMARY_REDIS_DURATION = 72000

    # all sector types list
    SECTOR_LIST = ["Industrials", "Consumer Cyclical", "Financial Services", "Utilities", "Basic Materials",
                   "Healthcare", "Energy", "Real Estate"]

    # max number of stocks fetch for each sector
    LIMIT_STOCK_PER_SECTOR = 10

    # stock indexes for turkish stock market
    TR_STOCK_INDEXES = ["XU100.IS", "XU030.IS", "XBANK.IS", "XUSIN.IS", "XUTEK.IS", "XUTUM.IS"]
    # precious metal symbols
    COMMODITY_TICKERS = [
        "GC=F",  # Gold
        "SI=F",  # Silver
        "PL=F",  # Platinum
        "HG=F",  # Copper
        "CL=F",  # Crude Oil
        "BZ=F",  # Brent Crude Oil
        "NG=F",  # Natural Gas
        "TRY=X"  # USD/TRY
    ]


settings = Settings()
