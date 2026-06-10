from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()


class Settings():




    DATABASE_URL = os.getenv("POSTRESQL_DATABASE_URL")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_HOST = os.getenv("REDIS_HOST")

    # DATABASE_URL = os.getenv("LOCALHOST_POSTRESQL_DATABASE_URL")
    # REDIS_PORT = os.getenv("REDIS_PORT")
    # REDIS_HOST = os.getenv("LOCAL_REDIS_HOST")




    #base project path
    BASE_DIR = Path(__file__).resolve().parent
    #base seeding part
    DATA_DIR = BASE_DIR / "data"

    STOCK_SEED_FILEPATH = DATA_DIR / "seed_database.json"

    #chunk size for daily update function
    DAILY_UPDATE_CHUNK_SIZE = 20
    #sleep time (seconds) between chunks for daily update function
    DAILY_UPDATE_SLEEP_TIME = 1
    #time between jobs (days) for daily update function
    DAILY_UPDATE_TIME_BETWEEN_JOBS = 1

    #chunk size for realtime update function
    REALTIME_UPDATE_CHUNK_SIZE = 50
    #sleep time (seconds) between chunks for realtime update function
    REALTIME_UPDATE_SLEEP_TIME = 0.5
    #time between jobs (minutes) for realtime update function
    REALTIME_UPDATE_TIME_BETWEEN_JOBS = 240

    #chunk size for longtime update function
    LONGTIME_UPDATE_CHUNK_SIZE = 50
    #sleep time (seconds) between chunks for longtime update function
    LONGTIME_UPDATE_SLEEP_TIME = 5
    #time between jobs (days) for longtime update function
    LONGTIME_UPDATE_TIME_BETWEEN_JOBS = 3

    #chunk size for very longtime update function
    VERY_LONG_TIME_CHUNK_SIZE = 50
    #sleep time (seconds) between chunks for very longtime update function
    VERY_LONGTIME_UPDATE_SLEEP_TIME = 10
    #time between jobs (days) for very longtime update function
    VERY_LONGTIME_UPDATE_TIME_BETWEEN_JOBS = 7

    # -- Update stats --

    """
    example stats:
    {
    "name_of_table_column":"name_of_yfinance.info_or_yfinance.fast_info_attribute"
    }
    """

    VERY_LONGTIME_UPDATE_STATS = {
        "eps": "trailingEps",
        "sector": "sector",
        "summary": "longBusinessSummary",
        "symbol": "symbol"

    }

    # LONGTIME_UPDATE_STATS = {
    #
    #     "yearHigh": "year_high",
    #     "yearLow": "year_low",
    #     "trailingPE":"trailingPE",
    #     "forwardPE":"forwardPE",
    #     "priceToBook":"priceToBook",
    #     "enterpriseToEbitda":"enterpriseToEbitda",
    #     "currentRatio":"currentRatio",
    #     "debtToEquity":"debtToEquity",
    #     "returnOnEquity":"returnOnEquity",
    #     "returnOnAssets":"returnOnAssets",
    # }
    # DAILY_UPDATE_STATS = {
    #     "previousClose": "previous_close",
    #     "dayHigh":"day_high",
    #     "dayLow":"day_low",
    #     "volume":"last_volume",
    #     "open": "open",
    #     "marketCap": "market_cap",
    #
    #     "avgVolume10Days":"ten_day_average_volume",
    #
    #     "avgVolume3Months":"three_month_average_volume",
    #
    #
    # }

    DAILY_UPDATE_STATS = {

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
        "lastVolume":"last_volume"
    }

    LONGTIME_UPDATE_STATS = {
        "forwardPE": "forwardPE",
        "priceToBook": "priceToBook",
        "enterpriseToEbitda": "enterpriseToEbitda",
        "currentRatio": "currentRatio",
        "debtToEquity": "debtToEquity",
        "returnOnEquity": "returnOnEquity",
        "returnOnAssets": "returnOnAssets",
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

    # Merge of all configs for longtime updater jobs
    stock_update_jobs_config = [
        {
            "days": DAILY_UPDATE_TIME_BETWEEN_JOBS,
            "stats": DAILY_UPDATE_STATS,
            "jobtype": DAILY_UPDATE_JOBNAME,
            "chunk_size": DAILY_UPDATE_CHUNK_SIZE,
            "sleep_time": DAILY_UPDATE_SLEEP_TIME,
            "use_fast_info": True
        },
        {
            "days": LONGTIME_UPDATE_TIME_BETWEEN_JOBS,
            "stats": LONGTIME_UPDATE_STATS,
            "jobtype": LONGTIME_UPDATE_JOBNAME,
            "chunk_size": LONGTIME_UPDATE_CHUNK_SIZE,
            "sleep_time": LONGTIME_UPDATE_SLEEP_TIME,
            "use_fast_info": False
        },
        {
            "days": VERY_LONGTIME_UPDATE_TIME_BETWEEN_JOBS,
            "stats": VERY_LONGTIME_UPDATE_STATS,
            "jobtype": VERY_LONGTIME_UPDATE_JOBNAME,
            "chunk_size": VERY_LONG_TIME_CHUNK_SIZE,
            "sleep_time": VERY_LONGTIME_UPDATE_SLEEP_TIME,
            "use_fast_info": False
        }
    ]

    # AI summary redis duration(seconds)
    AI_SUMMARY_REDIS_DURATION = 72000


settings = Settings()
