import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from contextlib import asynccontextmanager
from project.api.repository.stocks_repo import StockRepository
from project.api.routes.analysis_route import limiter
from project.api.routes import analysis_route, stocks_route
from project.logic.exceptions import StockNotFoundException, YfinanceApiException
from project.api.database import create_db_table
from project.api.base_models import StockStats
from settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    #initialize db
    create_db_table()
    logger.info("Database successfully initialized")

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        StockRepository.daily_job, trigger="date",
        kwargs={
            "database_model": StockStats, "chunk_size": settings.VERY_LONG_TIME_CHUNK_SIZE,
            "sleep_time": settings.VERY_LONGTIME_UPDATE_SLEEP_TIME,
            "stats": settings.VERY_LONGTIME_UPDATE_STATS,
            "use_fast_info": False,

        }
    )


    scheduler.add_job(
        StockRepository.daily_job, trigger="date",
        kwargs={
            "database_model": StockStats, "chunk_size": settings.DAILY_UPDATE_CHUNK_SIZE,
            "sleep_time": settings.DAILY_UPDATE_SLEEP_TIME,
            "stats": settings.DAILY_UPDATE_STATS

        }
    )
    scheduler.add_job(
        StockRepository.daily_job, trigger="date",
        kwargs={
            "database_model": StockStats, "chunk_size": settings.LONGTIME_UPDATE_CHUNK_SIZE,
            "sleep_time": settings.LONGTIME_UPDATE_SLEEP_TIME,
            "stats": settings.LONGTIME_UPDATE_STATS

        }
    )



    scheduler.add_job(
        StockRepository.update_realtime_stock_highlights,
        trigger="date",
        kwargs={"database_model": StockStats, "chunk_size": settings.REALTIME_UPDATE_CHUNK_SIZE,
                "sleep_time": settings.REALTIME_UPDATE_SLEEP_TIME}
    )

    scheduler.add_job(
        StockRepository.update_realtime_stock_highlights,
        trigger="interval",
        minutes=settings.REALTIME_UPDATE_TIME_BETWEEN_JOBS,
        kwargs={"database_model": StockStats, "chunk_size": settings.REALTIME_UPDATE_CHUNK_SIZE,
                "sleep_time": settings.REALTIME_UPDATE_SLEEP_TIME,

                }
    )

    scheduler.add_job(
        StockRepository.daily_job, trigger="interval", days=settings.DAILY_UPDATE_TIME_BETWEEN_JOBS, kwargs={
            "database_model": StockStats, "chunk_size": settings.DAILY_UPDATE_CHUNK_SIZE,
            "sleep_time": settings.DAILY_UPDATE_SLEEP_TIME,
            "stats": settings.DAILY_UPDATE_STATS
        }
    )
    scheduler.add_job(
        StockRepository.daily_job, trigger="interval", days=settings.LONGTIME_UPDATE_TIME_BETWEEN_JOBS, kwargs={
            "database_model": StockStats, "chunk_size": settings.LONGTIME_UPDATE_CHUNK_SIZE,
            "sleep_time": settings.LONGTIME_UPDATE_SLEEP_TIME,
            "stats": settings.LONGTIME_UPDATE_STATS

        }
    )
    scheduler.add_job(
        StockRepository.daily_job, trigger="interval", days=settings.VERY_LONGTIME_UPDATE_TIME_BETWEEN_JOBS,
        kwargs={
            "database_model": StockStats, "chunk_size": settings.VERY_LONG_TIME_CHUNK_SIZE,
            "sleep_time": settings.VERY_LONGTIME_UPDATE_SLEEP_TIME,
            "stats": settings.VERY_LONGTIME_UPDATE_STATS,
            "use_fast_info": False,

        }
    )

    scheduler.start()

    yield
    # it closes the scheduler when app is closed
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # 1. BAŞLANGIÇ: İstek ulaştı
    start_time = time.time()
    logger.info(f"Incoming request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # 2. BİTİŞ: İstek tamamlandı
        process_time = (time.time() - start_time) * 1000  # ms cinsinden
        logger.info(
            f"Completed: {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Duration: {process_time:.2f}ms"
        )
        return response

    except Exception as e:
        # Hata durumunda da log alıyoruz
        logger.error(f"Request failed: {str(e)}")
        raise e


@app.exception_handler(StockNotFoundException)
async def stock_not_found_exception_handler(request: Request, exc: StockNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"Error occurded : {exc.message} for ticker {exc.ticker}"}
    )


@app.exception_handler(YfinanceApiException)
async def yfinance_api_error_handler(request: Request, exc: YfinanceApiException):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.message, "technical_detail": exc.technical_detail}

    )


@app.get("/")
def initialize_api():
    return {"api_message": "Finpolar api initialized"}


app.include_router(analysis_route.router)
app.include_router(stocks_route.router)
