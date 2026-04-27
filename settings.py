from dotenv import load_dotenv
import os
load_dotenv()
class Settings():
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_HOST = os.getenv("REDIS_HOST" , "localhost")


settings = Settings()