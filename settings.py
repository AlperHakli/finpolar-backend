from dotenv import load_dotenv
import os
from pathlib import Path
load_dotenv()
class Settings():
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_HOST = os.getenv("REDIS_HOST" , "REDIS_LOCALHOST")

    #base project path
    BASE_DIR = Path(__file__).resolve().parent
    #base seeding part
    DATA_DIR = BASE_DIR / "data"

    STOCK_SEED_FILEPATH = DATA_DIR / "seed_database.json"



    #chunk size for daily update function
    DAILY_UPDATE_CHUNK_SIZE= 20
    #sleep time (seconds) between chunks for daily update function
    DAILY_UPDATE_SLEEP_TIME= 1
    #time between jobs (days) for daily update function
    DAILY_UPDATE_TIME_BETWEEN_JOBS=1


    #chunk size for realtime update function
    REALTIME_UPDATE_CHUNK_SIZE = 50
    #sleep time (seconds) between chunks for realtime update function
    REALTIME_UPDATE_SLEEP_TIME = 0.5
    #time between jobs (minutes) for realtime update function
    REALTIME_UPDATE_TIME_BETWEEN_JOBS = 5


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

    VERY_LONGTIME_UPDATE_STATS = {
        "eps": "trailingEps",
        "sector": "sector",
        "summary": "longBusinessSummary"

    }

    LONGTIME_UPDATE_STATS = {
        "marketCap":"market_cap",
        "year_high":"year_high",
        "year_low":"year_low",
    }
    DAILY_UPDATE_STATS = {
        "previous_close":"previous_close",
    }


    #these variables used when logging not important but necessary

    DAILY_UPDATE_LOGNAME="daily-update-job"
    LONGTIME_UPDATE_LOGNAME="longtime-update-job"
    VERY_LONGTIME_UPDATE_LOGNAME="very-longtime-update-job"








settings = Settings()