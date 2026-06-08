import logging
import os.path
import time
import asyncio
from typing import Callable, AsyncContextManager, Type
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from contextlib import asynccontextmanager

from project.api.redis_client import RedisClient, redis_manager
from project.api.repository.stocks_repo import StockRepository
from project.api.routes.analysis_route import limiter
from project.api.routes import analysis_route, stocks_route
from project.logic.exceptions import StockNotFoundException, YfinanceApiException, SeedFileNotFoundException
from project.api.database import create_db_table
from project.api.dependencies import get_postresql_db_ctx
from project.api.base_models import StockStats, StatBase
from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


class TaskAndJobWrappers():
    @staticmethod
    async def scheduled_pe_calc_wraps(
            database_session: Callable[[], AsyncContextManager],
            database_model: Type[StatBase]

    ):
        """
        wrapper for peratio calculator
        """
        async with database_session() as session:
            await StockRepository.recalculate_all_pe_ratios(database_session=session, database_model=database_model)

    @staticmethod
    async def update_realtime_stock_highlights_wraps(
            database_model: Type[StatBase],
            chunk_size: int,
            sleep_time: float,
            database_session: Callable[[], AsyncContextManager],
            redis_manager: RedisClient
    ):
        """
        wrapper for update realtime stock highlights
        """
        async with database_session() as session:
            await StockRepository.update_realtime_stock_highlights(
                database_model=database_model,
                database_session=session,
                redis_manager=redis_manager,
                chunk_size=chunk_size,
                sleep_time=sleep_time
            )

    @staticmethod
    async def universal_daily_job_wrapper(
            database_session: Callable[[], AsyncContextManager],
            **job_params  # kwargs
    ):
        """
        Shared async wrapper for all longtime tasks
        """
        async with database_session() as session:
            await StockRepository.daily_job(
                database_session=session,
                **job_params
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    #initialize db
    await create_db_table()
    await redis_manager.connect()
    app.state.redis = redis_manager

    logger.info("Database and Redis successfully initialized")

    scheduler = AsyncIOScheduler()

    #initializes db and inserts name and symbol
    async def initialize_db_wrapper():
        async with get_postresql_db_ctx() as session:
            await StockRepository.initialize_db(
                file_path=settings.STOCK_SEED_FILEPATH,
                database_session=session,
                database_model=StockStats,
            )

    await initialize_db_wrapper()

    logger.info("Database successfully seeded")

    logger.info("**** All parallel tasks have been started ****")

    async with asyncio.TaskGroup() as tg:
        for job_config in settings.stock_update_jobs_config:

            def create_parallel_task(config):
                async def task_wrapper():
                    async with get_postresql_db_ctx() as session:
                        await StockRepository.daily_job(
                            database_model=StockStats,
                            database_session=session,
                            chunk_size=config["chunk_size"],
                            sleep_time=config["sleep_time"],
                            stats=config["stats"],
                            jobtype=config["jobtype"],
                            use_fast_info=config["use_fast_info"]
                        )

                return task_wrapper

            tg.create_task(create_parallel_task(job_config)())

    logger.info("**** All parallel tasks have been completed ****")

    # -- Stock Highlights updater job --
    scheduler.add_job(
        TaskAndJobWrappers.update_realtime_stock_highlights_wraps,
        trigger="interval",
        next_run_time=datetime.now(),
        minutes=settings.REALTIME_UPDATE_TIME_BETWEEN_JOBS,
        kwargs={
            "database_model": StockStats, "chunk_size": settings.REALTIME_UPDATE_CHUNK_SIZE,
            "sleep_time": settings.REALTIME_UPDATE_SLEEP_TIME,
            "database_session": get_postresql_db_ctx,
            "redis_manager": redis_manager

        }
    )

    # -- All stock longtime updater jobs --
    for kwargs in settings.stock_update_jobs_config:
        jobkwargs = {
            **kwargs,
            "database_model": StockStats,
            "database_session": get_postresql_db_ctx,
        }

        days = jobkwargs.pop("days")

        scheduler.add_job(
            TaskAndJobWrappers.universal_daily_job_wrapper,
            trigger="interval",
            days=days,
            kwargs=jobkwargs

        )

    # -- peratio Calculator job for stocks --
    scheduler.add_job(
        TaskAndJobWrappers.scheduled_pe_calc_wraps,
        trigger="interval",
        next_run_time=datetime.now(),
        days=settings.DAILY_UPDATE_TIME_BETWEEN_JOBS,
        kwargs={
            "database_model": StockStats,
            "database_session": get_postresql_db_ctx,

        }
    )

    scheduler.start()

    yield
    # it closes the scheduler when app is closed
    await redis_manager.close()
    scheduler.shutdown(wait=True)
    logger.info("Application shutdown complete.")


app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter


app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(
        request: Request,
        call_next
):
    start_time = time.time()
    logger.info(f"Incoming request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)

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


# -- EXCEPTION HANDLERS --
@app.exception_handler(StockNotFoundException)
async def stock_not_found_exception_handler(
        request: Request,
        exc: StockNotFoundException
):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"Error occurded : {exc.message} for ticker {exc.ticker}"}
    )


@app.exception_handler(YfinanceApiException)
async def yfinance_api_error_handler(
        request: Request,
        exc: YfinanceApiException
):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.message, "technical_detail": exc.technical_detail}

    )


@app.exception_handler(SeedFileNotFoundException)
async def seed_file_not_found_handler(
        request: Request,
        exc: SeedFileNotFoundException
):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "initialization failed",
            "message": exc.message,
            "path": exc.file_path
        }

    )


@app.exception_handler(Exception)
async def global_exception_handler(
        request: Request,
        exc: Exception
):
    logger.critical(f"UNHANDLED CRITICAL ERROR: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": "Unhandled critical error occurded"
        }
    )


@app.get("/")
def initialize_api():
    logger.info("API has been initialized")
    return {"api_message": "Finpolar api initialized"}


app.include_router(analysis_route.router)
app.include_router(stocks_route.router)
