import asyncio
import json
import requests
import os.path
from collections import defaultdict
import yfinance
import logging
import polars as pl
import pandas as pd
from sqlmodel import select, update, func, Numeric, delete, col, over, or_
from project.logic.exceptions import StockNotFoundException, YfinanceApiException, SeedFileNotFoundException
from project.logic.utils import IndicatorCalculationUtils, HelperFunctions
from project.api.base_models import StockStats, GetSingleStockIndicatorModel, StatBase, AssetRouteBaseModels
from project.logic.indicator_service import IndicatorService
from project.api.redis_client import RedisClient
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# with this code yfinance thinks the program is real user
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

class StockRepository():
    from collections import defaultdict
    from typing import Any, Dict, List, Type

    from sqlalchemy import func
    from sqlmodel import select
    from sqlalchemy.sql import over

    @staticmethod
    async def get_multiple_stocks_by_sector_list(
            sector_list: list[str],
            database_session: AsyncSession,
            database_model: Type[StatBase] = StockStats,
            limit_per_sector: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        print(f"SECTOR LIST: {sector_list}")

        row_num = over(
            func.row_number(),
            partition_by=database_model.sector,
            order_by=func.random()
        ).label("row_num")

        subquery = (
            select(
                database_model.symbol.label("symbol"),
                database_model.name.label("name"),
                database_model.previousClose.label("previousClose"),
                database_model.open.label("open"),
                database_model.dayHigh.label("dayHigh"),
                database_model.dayLow.label("dayLow"),
                database_model.sector.label("sector"),
                database_model.lastVolume.label("lastVolume"),
                row_num,
            )
            .where(database_model.sector.in_(sector_list))
            .subquery()
        )

        stmt = (
            select(subquery)
            .where(subquery.c.row_num <= limit_per_sector)
        )

        result = await database_session.execute(stmt)
        rows = result.mappings().all()

        grouped_result = defaultdict(list)

        for row in rows:
            grouped_result[row["sector"]].append(
                {
                    "symbol": row["symbol"],
                    "name": row["name"],
                    "previousClose": row["previousClose"],
                    "open": row["open"],
                    "dayHigh": row["dayHigh"],
                    "dayLow": row["dayLow"],
                    "lastVolume": row["lastVolume"],
                }
            )

        return dict(grouped_result)

    @staticmethod
    async def search_asset_service(search_key: str, database_session: AsyncSession, database_model: type[StatBase]):
        """
        :param database_session: current postresql session
        :return: five of asset that most like search key
        """
        formatted_search = f"%{search_key.strip()}%"
        statement = (select(database_model.name, database_model.symbol)
                     .where(
            or_(
                database_model.symbol.ilike(formatted_search)
                , database_model.name.ilike(formatted_search)
            )
        ).limit(5))
        result = await database_session.execute(statement)
        resultfinal = result.mappings().all()

        return resultfinal

    @staticmethod
    async def get_random_10_assets_from_all_asset_types(database_session: AsyncSession , database_models: list[StatBase]):
        try:
            responsedict= {}
            for model in database_models:
                responsedict[model.__tablename__] = await StockRepository.get_random_10_assets(database_session=database_session , database_model=model)
            return {"status" : "success" , "count" : len(responsedict) , "data" : responsedict}

        except Exception as e:
            logger.error(f"An error occurded {e}")
            raise

    @staticmethod
    async def get_random_10_assets(database_session: AsyncSession , database_model: StatBase):
        try:
            statement = select(database_model).order_by(func.random()).limit(10)
            response = await database_session.execute(statement)
            rows = response.scalars().all()
            responselist = []
            for row in rows:
                responselist.append(

                    {
                        "symbol": row.symbol,
                        "name": row.name,
                        "previousClose": row.previousClose,
                        "open": row.open,
                        "dayHigh": row.dayHigh,
                        "dayLow": row.dayLow,
                    }

                )

            return responselist

        except Exception as e:
            logger.error(f"An error occurded {e}")
            raise



    @staticmethod
    async def get_top_10_with_details(redis_manager, database_session: AsyncSession):
        """
        Return top 10 volumed assets with more detailed informations
        :param redis_manager: redis db that contain market:top_volume
        :param database_session: postresql database that contain stock informations
        :return: top 10 volumed stocks with these informations:

                    "symbol": detail.symbol,
                    "name": detail.name,
                    "open": detail.open,
                    "dayHigh": detail.dayHigh,
                    "dayLow": detail.dayLow,
                    "previousClose": detail.previousClose,
                    "sector": detail.sector,
                    "lastVolume": detail.lastVolume

        """

        cached_watchlist = await redis_manager.getRedis("market:top_volume")

        if not cached_watchlist:
            return []

        ticker_names = [item["symbol"] for item in cached_watchlist]

        statement = select(StockStats).where(StockStats.symbol.in_(ticker_names))
        result = await database_session.execute(statement)
        db_details = result.scalars().all()

        enriched_list = []
        for detail in db_details:
            enriched_list.append(
                {
                    "symbol": detail.symbol,
                    "name": detail.name,
                    "open": detail.open,
                    "dayHigh": detail.dayHigh,
                    "dayLow": detail.dayLow,
                    "previousClose": detail.previousClose,
                    "sector": detail.sector,
                    "lastVolume": detail.lastVolume
                }
            )

        return enriched_list

    @staticmethod
    async def get_single_asset(
            symbol: str,
            database_session: AsyncSession,
            database_model: type[StatBase] = StockStats,
    ) -> dict:
        """
        Fetch Information about an asset from persistent database (except history)
        :param symbol: symbol of relevant asset
        :param database_session: current database session
        :param database_model: database table model
        :return: a dictionary contains single row with respect to given symbol
        """

        try:

            statement = select(database_model).where(database_model.symbol == symbol)
            result = await database_session.execute(statement)

            asset = result.scalar_one_or_none()

            if not asset:
                raise StockNotFoundException(message=f"No stock data found with given database", ticker=symbol)

            return asset.model_dump(exclude=["id"])


        except StockNotFoundException:
            logger.warning(f"Invalid or missing ticker when get_single_stock : {symbol}")
            raise

    @staticmethod
    async def get_single_asset_realtime_data(
            symbol: str,
            redis_manager: RedisClient,
            stats: list[str]

    ) -> dict:
        """
        Fetch real time information about an asset from redis database or yfinance
        :param redis_manager: redis database manager
        :param symbol: relevant asset's symbol
        :param stats: stats that will fetch from yfinance.fast_info must same with yfinance.fast_info attributes
        """
        attributes = {}
        missing_stats = []
        for stat in stats:
            result = await redis_manager.getRedis(f"stock:{symbol}:{stat}")
            if result is not None:
                attributes[stat] = result
            else:
                missing_stats.append(stat)

        if missing_stats:
            def get_info(missing_stats_inner: list[str], symbol: str):
                fresh_data = {}
                info = yfinance.Ticker(ticker=symbol , session=session).fast_info
                for stat in missing_stats_inner:
                    try:
                        val = info.__getattribute__(stat)
                        if val is not None:
                            fresh_data[stat] = val
                    except Exception:
                        continue
                return fresh_data

            new_data = await asyncio.to_thread(get_info, missing_stats, symbol)
            redis_tasks = []
            for stat, val in new_data.items():
                attributes[stat] = val
                redis_tasks.append(redis_manager.setRedis(f"stock:{symbol}:{stat}", val, exp=30))
            if redis_tasks:
                await asyncio.gather(*redis_tasks)

        return attributes

    @staticmethod
    async def get_single_asset_information_master(
            symbol: str,
            database_model: type[StatBase],
            database_session: AsyncSession,
            redis_manager: RedisClient,
            redis_stats: list[str],
    ):
        """
        Fetch and Merge single stock postresql data and redis data
        :param symbol: symbol of asset
        :param redis_stats: redis will use this list's elements as keys
        :param database_model: table model of persistent database
        """

        redisresult = await StockRepository.get_single_asset_realtime_data(symbol=symbol, stats=redis_stats, redis_manager=redis_manager)
        dbresult = await StockRepository.get_single_asset(symbol=symbol, database_session=database_session, database_model=database_model)

        currentPrice = redisresult.get("last_price", 0.0)
        previousClose = dbresult.get("previousClose", 0.0)

        if previousClose == 0:

            changePercent = 0.0
        else:
            changePercent = IndicatorCalculationUtils.change_percent_calculator(currentPrice, previousClose)

        changeDigit = currentPrice - previousClose
        if changeDigit == 0:
            await redis_manager.setRedisNoDict(f"stock:{symbol}:last_price", currentPrice, exp=7200)

        newdict = {"changeDigit": changeDigit, "changePercent": changePercent}

        return redisresult | dbresult | newdict

    @staticmethod
    async def get_multiple_asset_history(payload: list[AssetRouteBaseModels.AssetHistoryRequestModel])\
            -> dict:
        """
        Fetch multiple asset history with given tickerlist and period
        :param payload: ticker and period list
        example payload:
        [
            {"ticker": "THYAO.IS", "period": "1d"},
            {"ticker": "GC=F", "period": "1mo"}
        ]

        """
        try:
            response = {}
            for item in payload:

                history = await StockRepository.get_single_asset_history(ticker=item.ticker, period=item.period)
                tickerdict = {"symbol": item.ticker}
                historydict= {"history": history.get("history")}
                perioddict = {"period" : item.period}
                response[item.ticker] = tickerdict | historydict | perioddict



            return {"status": "success" , "count" : len(response) , "data": response}


        except Exception as e:
            logger.error(f"Error get_multiple_asset_history ")
            raise

    @staticmethod
    async def get_single_asset_history(ticker: str, period: str)\
            -> dict:
        """
        Fetch history data of asset
        :param ticker: symbol of relevant asset
        :param period: history period of relevant asset available (1d , 5d , 1mo , 2mo , 6mo , 1y , 10y)
        :return: stock history with respect to given period
        """
        try:

            df = await StockRepository._fetch_raw_asset_history(ticker=ticker, period=period)

            time_col = "Date" if "Date" in df.columns else "Datetime"

            history = df.select(
                [
                    pl.col(time_col).dt.strftime("%Y-%m-%d" if time_col == "Date" else "%Y-%m-%d %H:%M").alias("date"),
                    pl.col("Close").round(3).alias("price")
                ]
            ).to_dicts()

            return {"history": history}

        except StockNotFoundException:
            logger.warning(f"Invalid or missing ticker when get_single_stock : {ticker}")
            raise
        except Exception as e:
            logger.error(f"Error get_single_stock_history {ticker}")
            raise YfinanceApiException(technical_detail=str(e))

    @staticmethod
    async def _fetch_raw_asset_history(ticker: str, period: str):
        """
        Fetch data from yfinance returns raw polars dataframe
        """

        interval = IndicatorCalculationUtils.interval_calculator(period=period)

        df_pd = await asyncio.to_thread(HelperFunctions.fetch_history, ticker, period, interval)

        if df_pd.empty:
            raise StockNotFoundException(ticker=ticker, message="History not found")

        # convert to polars from pandas and convert index(date) to column
        return pl.from_pandas(df_pd.reset_index())

    @staticmethod
    async def get_watchlist(redis_manager: RedisClient) -> dict:
        """

        :param redis_manager: redis database manager
        :return:complete watchlist
        """
        tempdict = {
            "top_volume": await redis_manager.getRedis("market:top_volume"),
            "top_gainers": await redis_manager.getRedis("market:top_gainers"),
            "top_losers": await redis_manager.getRedis("market:top_losers")
        }
        return tempdict

    @staticmethod
    async def update_realtime_data(
            database_model: Type[StatBase],
            database_session: AsyncSession,
            redis_manager: RedisClient,
            stock_indexes: list[str],
            chunk_size: int = 100,
            sleep_time: float = 0.5
    ):
        """
        Updates Realtime data like top 10 stocks

        Uses both redis and postresql
        uses current_price from redis
        uses previousClose , name and symbol from postresql


        :param database_model: database table model
        :param database_session: current database session
        :param redis_manager: redis database manager
        :param stock_indexes: stock market indexes that will update
        :param chunk_size: determines how many assets will begin to process in single time
        :param sleep_time: duration between chunks
        """
        async with asyncio.TaskGroup() as tg:
            tg.create_task(
                StockRepository.update_top_stocks(
                    database_model=database_model,
                    database_session=database_session,
                    redis_manager=redis_manager,
                    chunk_size=chunk_size,
                    sleep_time=sleep_time
                )
            )

            tg.create_task(
                StockRepository.update_stock_market_index(
                    redis_manager=redis_manager,
                    stock_indexes=stock_indexes,
                    database_session=database_session,
                    database_model=database_model
                )

            )

    @staticmethod
    async def update_top_stocks(
            database_model: Type[StatBase],
            database_session: AsyncSession,
            redis_manager: RedisClient,
            chunk_size: int = 100,
            sleep_time: float = 0.5

    ):

        """Uses both redis and postresql
        uses current_price from redis
        uses previousClose , name and symbol from postresql


        :param database_model: database table model
        :param database_session: current database session
        :param redis_manager: redis database manager

        :param chunk_size: determines how many assets will begin to process in single time
        :param sleep_time: duration between chunks"""
        try:
            # if not IndicatorCalculationUtils.work_time_controller():
            #     return

            sleep_time_rnd_added = IndicatorCalculationUtils.add_random_seconds_to_sleep_time_between_chunks(sleep_time=sleep_time)

            statement = select(database_model)
            result = await database_session.execute(statement)
            all_stocks = result.scalars().all()

            if not all_stocks:
                logger.error("No stocks found in database to update highlights")
                return

            stat_list = []
            symbols = [s.symbol for s in all_stocks]

            prev_close_map = {s.symbol: s.previousClose for s in all_stocks}
            name_map = {s.symbol: s.name for s in all_stocks}

            for i in range(0, len(symbols), chunk_size):
                chunk = symbols[i: i + chunk_size]
                logger.info(f"Realtime processing chunk: {len(chunk)} symbols")

                data = await asyncio.to_thread(HelperFunctions.fetch_1d_history, chunk)

                if data.empty:
                    logger.error("yfinance data is empty on update_realtime_stock_highlights")
                    continue

                for ticker in chunk:
                    try:
                        if ticker not in data or data[ticker].empty:
                            continue

                        stock = data[ticker]
                        current_close = stock["Close"].iloc[-1]
                        volume = stock["Volume"].iloc[-1]

                        prev_close = prev_close_map.get(ticker)

                        stock_name = name_map.get(ticker)

                        if pd.isna(volume) or pd.isna(current_close) or volume <= 0 or not prev_close:
                            continue

                        trade_value = volume * current_close

                        change_percent = IndicatorCalculationUtils.change_percent_calculator(current_close=current_close, prev_close=prev_close)

                        stat_list.append(
                            {
                                "symbol": ticker,
                                "name": stock_name,
                                "price": round(float(current_close), 2),
                                "trade_value": float(trade_value),
                                "changePercent": round(float(change_percent), 2),
                            }
                        )

                    except Exception as inner_e:
                        logger.warning(f"Error processing {ticker} in realtime: {inner_e}")
                logger.info(f"Realtime processing chunk: {len(chunk)} symbols has been successfully completed")

                await asyncio.sleep(sleep_time_rnd_added)

            if not stat_list:
                logger.error("stat list is empty on update_realtime_stock_highlights")
                return

            #sortings
            top_volume = sorted(stat_list, key=lambda x: x["trade_value"], reverse=True)[:10]
            top_gainers = sorted(stat_list, key=lambda x: x["changePercent"], reverse=True)[:10]
            top_losers = sorted(stat_list, key=lambda x: x["changePercent"])[:10]

            #write to redis

            await redis_manager.setRedisNoExp(name="market:top_volume", value=top_volume)
            await redis_manager.setRedisNoExp(name="market:top_gainers", value=top_gainers)
            await redis_manager.setRedisNoExp(name="market:top_losers", value=top_losers)

            logger.info(f"Highlights updated successfully with {len(stat_list)} stocks.")

        except Exception as e:
            logger.error(f"Realtime highlights error: {e}")

    @staticmethod
    async def get_market_indices_service(redis_manager: RedisClient):
        cache_key = "stock-index:TR"
        return await redis_manager.getRedis(cache_key)

    @staticmethod
    async def update_stock_market_index(
            redis_manager: RedisClient,
            stock_indexes: list[str],
            database_model: Type[StatBase],
            database_session: AsyncSession,
    ):
        cache_key = "stock-index:TR"
        temp_info = []

        statement = select(database_model).where(database_model.symbol.in_(stock_indexes))
        execution = await database_session.execute(statement)

        db_stocks_map = {stock.symbol: stock for stock in execution.scalars().all()}

        for symbol in stock_indexes:
            try:

                ticker = yfinance.Ticker(symbol , session=session)
                info = ticker.info

                lastPrice = info.get("regularMarketPrice")
                previousClose = info.get("regularMarketPreviousClose")
                name = info.get("shortName", symbol)

                if lastPrice is None or previousClose is None:
                    logger.warning(f"yfinance {symbol} için boş döndü. DB fallback devreye giriyor...")
                    db_result = db_stocks_map.get(symbol)

                    if db_result and db_result.previousClose:
                        lastPrice = db_result.previousClose
                        previousClose = db_result.previousClose
                    else:

                        lastPrice = 0.0
                        previousClose = 0.0

                changeDigit = lastPrice - previousClose
                changePercent = IndicatorCalculationUtils.change_percent_calculator(
                    current_close=lastPrice,
                    prev_close=previousClose
                )

                temp_info.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "lastPrice": lastPrice,
                        "previousClose": previousClose,
                        "changeDigit": changeDigit,
                        "changePercent": changePercent,
                    }
                )

            except Exception as e:
                logger.error(f"{symbol} endeksi işlenirken hata oluştu, pas geçiliyor: {e}")
                continue

        await redis_manager.setRedisNoDictNoExp(name=cache_key, value=json.dumps(temp_info))
        logger.info("Endeks verileri başarıyla Redis'e yazıldı.")

    @staticmethod
    async def _fetch_symbols_from_database(
            database_model: Type[StatBase],
            database_session: AsyncSession

    ) -> list[str]:
        """
        fetch only symbols from all assets
        :param database_model: database table model
        :param database_session: current database session
        :return: symbol list
        """

        statement = select(database_model.symbol)
        execution = await database_session.execute(statement)
        result = execution.scalars().all()
        return result

    @staticmethod
    async def _update_long_time_ticker_metrics(
            chunk_size: int,
            sleep_time: int,
            symbols: list[str],
            database_model: Type[StatBase],
            database_session: AsyncSession,
            stats: dict,
            jobtype: str,
            use_fast_info: bool,
    ):

        """
        Updates long time stock redis_stats
        :param use_fast_info: determines the function will use ticker.info or ticker.get_fast_info (if true is uses get_fast_info)
        :param chunk_size: size of each batch when downloading data from yfinance
        :param sleep_time: wait time between each batch (seconds)
        :param symbols: symbols of stocks , crypto etc.
        :param database_model: database table model
        :param redis_stats: redis_stats that will update example: {"stat_name_at_database_model":"stat_name_at_yfinance_info or stat_name_at_yfinance.fast_info"}
        :return:
        """

        def fetch_info(inner_ticker: yfinance.Ticker, inner_use_fast_info: bool, inner_stats: dict) -> dict:
            """
            fetch info from yfinance with respect to given stats
            """
            value = {}
            if inner_use_fast_info:
                info = inner_ticker.fast_info
                for db_column, yf_field in inner_stats.items():
                    value[db_column] = info.__getattribute__(yf_field)

            else:
                info = dict(inner_ticker.info)
                for db_column, yf_field in inner_stats.items():
                    value[db_column] = info.get(yf_field)

            return value

        try:

            for i in range(0, len(symbols), chunk_size):
                chunk = symbols[i: i + chunk_size]
                remaining = len(symbols) - (i + len(chunk))
                logger.info(f"Processing chunk on {jobtype}: {len(chunk)} symbols")

                for symbol in chunk:
                    try:
                        ticker = yfinance.Ticker(ticker=symbol , session=session)

                        value = await asyncio.to_thread(fetch_info, ticker, use_fast_info, stats)

                        if value is not None:
                            formatted_value = IndicatorCalculationUtils.format_orchestrator(data=value)
                            statement = (
                                update(database_model)
                                .where(database_model.symbol == symbol)
                                .values(**formatted_value)
                            )
                            await database_session.execute(statement)


                    except Exception as inner_e:
                        logger.warning(f"Error fetch info for {symbol}: {inner_e}")
                remaining = remaining - chunk_size
                await database_session.commit()
                logger.info(f"Chunk jobname: {jobtype} has been completed remaining assets: {remaining} ")
                await asyncio.sleep(sleep_time)


        except Exception as e:
            logger.error(f"Global error in _update_long_time_ticker_metrics: {e}")
            raise e

    @staticmethod
    async def recalculate_all_pe_ratios(
            database_session: AsyncSession,
            database_model: Type[StatBase] = StockStats,

    ):
        statement = (update(database_model).
                     where(database_model.eps.is_not(None), database_model.eps != 0).
                     values(trailingPE=func.round(func.cast(database_model.previousClose, Numeric) / func.cast(database_model.eps, Numeric), 2)))

        results = await database_session.execute(statement)

        await database_session.commit()
        logger.info("All PE Ratios recalculated successfully via Raw SQL.")

    @staticmethod
    async def daily_job(
            database_model: Type[StatBase],
            database_session: AsyncSession,
            chunk_size: int,
            sleep_time: int,
            stats: dict,
            jobtype: str,
            use_fast_info: bool = True
    ):

        """
        Uses yfinance_info or yfinance.get_fast_info to updates stock redis_stats

        :param use_fast_info: determines the function will use ticker.info or ticker.get_fast_info (if true is uses get_fast_info)
        :param database_model: table model of database
        :param database_session: current database session
        :param chunk_size: batch size when download stock data from yfinance
        :param sleep_time: sleep time between each batch
        :param redis_stats: redis_stats that will update example: {"stat_name_at_database_model":"stat_name_at_yfinance_info"}
        :param jobtype: type of job when debugging daily , longtime or very long time
        :return:
        """
        logger.info(f"----------------- {jobtype} has been started .. -----------------")
        logger.info(f"{jobtype} with stats: sleep_time {sleep_time} , chunk_size {chunk_size}")
        symbols = await StockRepository._fetch_symbols_from_database(database_model=database_model, database_session=database_session)

        await StockRepository._update_long_time_ticker_metrics(
            chunk_size=chunk_size,
            sleep_time=sleep_time,
            symbols=symbols,
            database_model=database_model,
            database_session=database_session,
            stats=stats,
            jobtype=jobtype,
            use_fast_info=use_fast_info
        )

        logger.info(f"----------------- {jobtype} has been done successfully -----------------")

    @staticmethod
    async def get_single_stock_indicators(
            redis_manager: RedisClient,
            indicator_settings: GetSingleStockIndicatorModel
    ) -> dict:
        """
        Calculates multiple indicators for a single stock using an atomic caching strategy.
        Only computes indicators that are missing from Redis.
        """
        try:
            ticker = indicator_settings.ticker.upper()
            period = indicator_settings.period
            s = indicator_settings.model_dump()

            # creating unique indicator keys
            keys = {
                "rsi": f"stock_indicator:RSI:{ticker}:{s['rsi_period']}:{period}",
                "macd": f"stock_indicator:MACD:{ticker}:{s['macd_fast']}_{s['macd_slow']}_{s['macd_signal']}:{period}",
                "bb": f"stock_indicator:BB:{ticker}:{s['bb_period']}_{s['bb_std_dev']}:{period}",
                "ma": f"stock_indicator:MA:{ticker}:{s['ma_short']}_{s['ma_long']}:{period}",
                "rvol": f"stock_indicator:RVOL:{ticker}:{period}"
            }
            #fetch caches
            cached_data = {
                "rsi": await redis_manager.getRedis(keys["rsi"]),
                "macd": await redis_manager.getRedis(keys["macd"]),
                "bb": await redis_manager.getRedis(keys["bb"]),
                "ma": await redis_manager.getRedis(keys["ma"]),
                "rvol": await redis_manager.getRedis(keys["rvol"])
            }

            missing_indicators = [name for name, val in cached_data.items() if not val]

            if not missing_indicators:
                logger.info(f"Cache HIT for all indicators of {ticker} ({period})")
                return {
                    "rsi": cached_data["rsi"],
                    "moving_averages": cached_data["ma"],
                    "bollinger_bands": cached_data["bb"],
                    "macd": cached_data["macd"],
                    "volume_analysis": cached_data["rvol"]
                }

            logger.info(f"Cache MISS on indicators: {missing_indicators}. Fetching data from DB...")
            df = await StockRepository._fetch_raw_asset_history(ticker=ticker, period=period)

            if df is None or len(df) == 0:
                logger.warning(f"No price data found for {ticker}")
                return {}

            tasks = {}
            if "rsi" in missing_indicators:
                tasks["rsi"] = IndicatorService.compute_rsi_logic(df, period=s["rsi_period"])
            if "ma" in missing_indicators:
                tasks["ma"] = IndicatorService.compute_ma_logic(
                    df, short_window=s["ma_short"], long_window=s["ma_long"]
                )
            if "bb" in missing_indicators:
                tasks["bb"] = IndicatorService.compute_bollinger_logic(
                    df, period=s["bb_period"], std_dev=s["bb_std_dev"]
                )
            if "macd" in missing_indicators:
                tasks["macd"] = IndicatorService.compute_macd_logic(
                    df, fast=s["macd_fast"], slow=s["macd_slow"], signal=s["macd_signal"]
                )
            if "rvol" in missing_indicators:
                tasks["rvol"] = IndicatorService.compute_rvol_logic(df)

            calculated_results = {}
            if tasks:
                task_names = list(tasks.keys())
                executed_tasks = await asyncio.gather(*tasks.values())
                calculated_results = dict(zip(task_names, executed_tasks))

            for name, result in calculated_results.items():
                if result:
                    await redis_manager.setRedis(name=keys[name], value=result, exp=600)
                    cached_data[name] = result

            return {
                "rsi": cached_data["rsi"],
                "moving_averages": cached_data["ma"],
                "bollinger_bands": cached_data["bb"],
                "macd": cached_data["macd"],
                "volume_analysis": cached_data["rvol"]
            }

        except Exception as e:
            logger.error(f"An error occurred in get_single_stock_indicators: {e}")
            raise e

    @staticmethod
    async def seed_database(
            arguments: dict,
            database_session: AsyncSession,
            database_model: Type[StatBase],

    ):
        """
        Initialize Statbase with name and ticker code
        :param database_model: database table model
        :param database_session: current database session
        :param arguments: must be a dict ,  symbol as key and name as value e.g: {ticker_symbol:ticker_name}
        """
        logger.info(f"Synchronizing database {database_model} with JSON source...")

        statement = select(database_model.symbol)
        execution = await database_session.execute(statement)

        db_symbols = set(execution.scalars().all())

        json_symbols = set(arguments.keys())

        to_add_symbols = json_symbols - db_symbols
        templist = []
        for sym in to_add_symbols:
            templist.append(database_model(symbol=sym, name=arguments[sym]))

        if templist:
            database_session.add_all(templist)
            logger.info(f"Adding {len(templist)} new symbols.")

        to_delete_symbols = db_symbols - json_symbols
        if to_delete_symbols:
            delete_statement = delete(database_model).where(col(database_model.symbol).in_(to_delete_symbols))
            await database_session.execute(delete_statement)
            logger.info(f"Deleting {len(to_delete_symbols)} obsolete symbols.")

        await database_session.commit()
        logger.info(f"Sync completed for {database_model}.")

    @staticmethod
    async def load_initial_stocks(file_path: str) -> dict:
        """
        Fetch initial symbol and name from given json path
        parent directory of all json seed files is "data" directory

        :param file_path: path of relevant json file
        :return: dictionary converted from json
        """
        full_path = os.path.join("data", file_path)
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    async def initialize_db(
            file_path: str,
            database_model: Type[StatBase],
            database_session: AsyncSession

    ):
        """
        orchestrator function for load_initial_stocks and seed_database initializes database model
        :param database_session: current database session
        :param file_path: path of relevant json file
        :param database_model: relevant table model

        """
        results = await StockRepository.load_initial_stocks(file_path=file_path)
        if not results:
            logger.warning(f"Seed data has not been loaded either file_name is missing or empty")
            raise SeedFileNotFoundException

        await StockRepository.seed_database(
            arguments=results,
            database_model=database_model,
            database_session=database_session
        )
