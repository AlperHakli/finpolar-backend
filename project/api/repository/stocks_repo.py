import asyncio
import datetime
import json
import os
from typing import Type
from datetime import date
import yfinance
import logging
import hashlib
import polars as pl
import pandas as pd
import time

from sqlmodel import Session , select , update , func , Numeric
from project.logic.exceptions import StockNotFoundException, YfinanceApiException , SeedFileNotFoundException
from project.logic.utils import IndicatorCalculationUtils
from project.api.base_models import StockStats , GetSingleStockIndicatorModel , StatBase
from project.logic.indicator_service import IndicatorService
from project.api.redis_client import redis_manager
from project.api.database import engine
from sqlalchemy.ext.asyncio import AsyncSession




logger = logging.getLogger(__name__)


class StockRepository():
    @staticmethod
    async def get_single_asset(
            symbol: str,
            database_session: AsyncSession,
            database_model: type[StatBase] = StockStats,
    )->dict:
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

                asset = result.scalars().one_or_none()

                if not asset:
                    raise StockNotFoundException(message=f"No stock data found with given database")

                return asset.model_dump(exclude=["id"])


        except StockNotFoundException:
            logger.warning(f"Invalid or missing ticker when get_single_stock : {symbol}")
            raise


            # name = result.get("name")
            # previousClose = result.get("previousClose")
            # sector = result.get("sector")
            # marketcap = result.get("marketCap")
            # peRatio = result.get("trailingPE")
            # summary = result.get("summary", "No description available.")
            # symbol = result.get("symbol")
            # year_high = result.get("year_high")
            # year_low = result.get("year_low")



    @staticmethod
    async def get_single_asset_realtime_data(symbol: str, stats: list[str]) ->dict:
        """
        Fetch Information about an asset from redis database
        """
        attributes = {}
        missing_stats = []
        for stat in stats:
            result = redis_manager.getRedis(f"stock:{symbol}:{stat}")
            if result is not None:
                attributes[stat] = result
            else: missing_stats.append(stat)

        if missing_stats:
            def get_info(missing_stats_inner: list[str] , symbol: str):
                fresh_data = {}
                info = yfinance.Ticker(ticker=symbol).fast_info
                for stat in missing_stats_inner:
                    try:
                        val = info.__getattribute__(stat)
                        if val is not None:
                            fresh_data[stat] = val
                    except Exception:
                        continue
                return fresh_data

            new_data = await asyncio.to_thread(get_info , missing_stats , symbol)

            for stat, val in new_data.items():
                attributes[stat] = val

                redis_manager.setRedis(f"stock:{symbol}:{stat}", val, expire=30)

        return attributes
    @staticmethod
    async def get_single_stock_information_master(
            symbol:str,
            database_model:type[StatBase],
            redis_stats:list[str],
    ):
        """
        Merges both single stock postresql data and redis data
        :param symbol: symbol of asset
        :param redis_stats: redis will use this list's elements as keys
        :param database_model: table model of persistent database
        """

        redisresult = await StockRepository.get_single_asset_realtime_data(symbol=symbol, stats=redis_stats)
        dbresult = await StockRepository.get_single_asset(symbol=symbol , database_model=database_model)





        changePercent = IndicatorCalculationUtils.change_percent_calculator(current_close=currentPrice,
                                                                            prev_close=previousClose)
        short_summary = summary[:520] + "..." if len(summary) > 520 else summary
        short_marketcap = IndicatorCalculationUtils.format_market_cap(marketcap)
        formatted_symbol = IndicatorCalculationUtils.format_symbol(symbol)
        changeDigit_raw = currentPrice - previousClose
        changeDigit = f"{changeDigit_raw:.2f}"
        currentPrice_edited = f"{currentPrice:.2f}"

    @staticmethod
    async def get_single_stock_history(ticker: str, period: str):
        """
        Fetch only history data of stock
        :param ticker: symbol of relevant stock
        :param period: period (1mo , 1h , 1y etc.)
        :return: stock history with respect to given period
        """
        try:

            df = await StockRepository._fetch_raw_stock_df(ticker=ticker , period=period)

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
            logger.error(f"Error when get_single_stock_history {ticker}")
            raise YfinanceApiException(technical_detail=str(e))

    @staticmethod
    async def _fetch_raw_stock_df(ticker: str, period: str):
        """
        Fetch data from yfinance returns raw polars dataframe
        """
        if not ticker.endswith(".IS"):
            ticker += ".IS"

        interval = IndicatorCalculationUtils.interval_calculator(period=period)
        stock = yfinance.Ticker(ticker=ticker)
        df_pd = stock.history(period=period, interval=interval)

        if df_pd.empty:
            raise StockNotFoundException(ticker=ticker, message="History not found")

        # convert to polars from pandas and convert index(date) to column
        return pl.from_pandas(df_pd.reset_index())

    @staticmethod
    def get_watchlist(session: Session):
        try:
            tempdict = {
                "top_volume":redis_manager.getRedis("market:top_volume"),
                "top_gainers":redis_manager.getRedis("market:top_gainers"),
                "top_losers":redis_manager.getRedis("market:top_losers")

            }
            return tempdict



        except Exception as e:
            logger.error(f"An error occurded: {e}")
            raise e

    @staticmethod
    def update_realtime_stock_highlights(
            database_model: Type[StatBase],
            database_session:
            chunk_size: int = 100 ,
            sleep_time: float = 0.5):
        """
        Writes most increased and decreased 10 stocks and writes top 10 stocks that have the most volume to redis
        Updates trailingPE of stock
        """
        try:
            if not IndicatorCalculationUtils.work_time_controller():
                return
            sleep_time_rnd_added = IndicatorCalculationUtils.add_random_seconds_to_sleep_time_between_chunks(sleep_time=sleep_time)
            with Session(engine) as session:
                all_stocks = session.exec(select(database_model)).all()

            if not all_stocks:
                logger.error("No stocks found in database to update highlights")
                return

            stat_list = []
            symbols = [s.symbol for s in all_stocks]

            prev_close_map = {s.symbol: s.previous_close for s in all_stocks}
            name_map = {s.symbol :  s.name for s in all_stocks}


            for i in range(0, len(symbols), chunk_size):
                chunk = symbols[i: i + chunk_size]
                logger.info(f"Realtime processing chunk: {len(chunk)} symbols")


                data = yfinance.download(chunk, period="1d", group_by="ticker", progress=False)

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

                        change_percent = ((current_close - prev_close) / prev_close) * 100

                        stat_list.append(
                            {
                                "symbol": ticker.replace(".IS", ""),
                                "name": stock_name,
                                "price": round(float(current_close), 2),
                                "trade_value": float(trade_value),
                                "changePercent": round(float(change_percent), 2),
                            }
                        )
                    except Exception as inner_e:
                        logger.warning(f"Error processing {ticker} in realtime: {inner_e}")

                time.sleep(sleep_time_rnd_added)

            if not stat_list:
                logger.error("stat list is empty on update_realtime_stock_highlights")
                return

            #sortings
            top_volume = sorted(stat_list, key=lambda x: x["trade_value"], reverse=True)[:10]
            top_gainers = sorted(stat_list, key=lambda x: x["changePercent"], reverse=True)[:10]
            top_losers = sorted(stat_list, key=lambda x: x["changePercent"])[:10]

            #write to redis
            async def push_to_redis():
                await redis_manager.setRedisNoExp(name="market:top_volume", value=top_volume)
                await redis_manager.setRedisNoExp(name="market:top_gainers", value=top_gainers)
                await redis_manager.setRedisNoExp(name="market:top_losers", value=top_losers)

            asyncio.run(push_to_redis())

            logger.info(f"Highlights updated successfully with {len(stat_list)} stocks.")

        except Exception as e:
            logger.error(f"Realtime highlights error: {e}")

    @staticmethod
    def _fetch_symbols_from_postresql(database_model: Type[StatBase]) -> list[str]:
        """
        :param database_model: postresql table
        :return: symbol list
        """
        try:
            with Session(engine) as session:
                statement = select(database_model.symbol)
                result = session.exec(statement).all()
                return result
        except Exception as e:
            logger.error(f"An error occurded {e}")
            raise e


    @staticmethod
    def _update_long_time_ticker_metrics(
            chunk_size: int, sleep_time: int, symbols: list[str], database_model: Type[StatBase], stats: dict , jobtype: str ,  use_fast_info = True
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
        try:
            with Session(engine) as session:
                for i in range(0, len(symbols), chunk_size):
                    chunk = symbols[i: i + chunk_size]
                    logger.info(f"Processing chunk on {jobtype}: {len(chunk)} symbols")

                    for symbol in chunk:
                        try:
                            ticker = yfinance.Ticker(ticker=symbol)
                            info = ticker.fast_info if use_fast_info else ticker.info


                            update_values = {}
                            for db_column, yf_field in stats.items():

                                if use_fast_info:
                                    value = info.__getattribute__(yf_field)
                                else:
                                    value = info.get(yf_field)

                                if value is not None:
                                    if isinstance(value,
                                                  (float, int)):
                                        update_values[db_column] = round(float(value), 2)
                                    else:
                                        update_values[db_column] = value




                            if update_values:
                                statement = (
                                    update(database_model)
                                    .where(database_model.symbol == symbol)
                                    .values(**update_values)
                                )
                                session.exec(statement)

                        except Exception as inner_e:
                            logger.warning(f"Error fetching info for {symbol}: {inner_e}")


                    session.commit()
                    logger.info(f"Chunk completed and committed.")
                    time.sleep(sleep_time)

        except Exception as e:
            logger.error(f"Global error in _update_long_time_ticker_metrics: {e}")
            raise e

    @staticmethod
    def recalculate_all_pe_ratios(database_model : Type[StatBase] = StockStats):
        try:
            with (Session(engine) as session):

                statement = update(database_model).where(database_model.eps != None , database_model.eps != 0).values(peRatio=func.round(func.cast(database_model.previous_close , Numeric) / func.cast(database_model.eps , Numeric) , 2))

                results = session.exec(statement)

                session.commit()
                logger.info("All PE Ratios recalculated successfully via Raw SQL.")
        except Exception as e:
            logger.error(f"Error in calculate_pe_ratios: {e}")

    @staticmethod
    def daily_job(
            database_model: Type[StatBase],
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
        :param chunk_size: batch size when download stock data from yfinance
        :param sleep_time: sleep time between each batch
        :param redis_stats: redis_stats that will update example: {"stat_name_at_database_model":"stat_name_at_yfinance_info"}
        :param jobtype: type of job when debugging daily , longtime or very long time
        :return:
        """
        logger.info(f"----------------- {jobtype} has been started .. -----------------")
        logger.info(f"{jobtype } with redis_stats: {locals()}")
        symbols = StockRepository._fetch_symbols_from_postresql(database_model=database_model)

        StockRepository._update_long_time_ticker_metrics(
            chunk_size=chunk_size ,
            sleep_time=sleep_time ,
            database_model=database_model ,
            stats=stats ,
            symbols=symbols,
            jobtype=jobtype,
            use_fast_info=use_fast_info
        )

        # StockRepository._recalculate_all_pe_ratios()
        logger.info(f"----------------- {jobtype} has been done successfully -----------------")




    @staticmethod
    async def get_single_stock_indicators(ticker: str , period: str ,  indicator_settings: GetSingleStockIndicatorModel):
        "Calculates multiple indicator for single stock"
        try:
            ticker = ticker.upper()

            settings_dict = indicator_settings.model_dump()

            cache_data = {**settings_dict, "period": period}
            settings_json = json.dumps(cache_data , sort_keys=True)
            settings_hash = hashlib.md5(settings_json.encode()).hexdigest()


            cache_key = f"stock:{ticker}:settings:{settings_hash}"

            cached_val = redis_manager.getRedis(name=cache_key)

            if cached_val:
                logger.info("Cache hit on multiple indicator calculation")
                return cached_val
            logger.info("Cache miss on multiple indicator calculation calculating indicators ... ")



            df = await StockRepository._fetch_raw_stock_df(ticker=ticker, period=period)

            calculated_indicators = await IndicatorService.compute_all_logic(df=df, **settings_dict)

            logger.info("Multiple indicator calculation has been completed")

            await redis_manager.setRedis(name=cache_key, value=calculated_indicators)

            return calculated_indicators

        except Exception as e:
            logger.error(f"An error occurded: {e}")
            raise e


    @staticmethod
    def seed_database(arguments: dict,database_model: Type[StatBase]):
        """
        Initialize Statbase with name and ticker code
        :param arguments: dictionary type arguments e.g: {ticker_symbol:ticker_name}
        """
        try:
            with Session(engine) as session:
                statement = select(func.count()).select_from(database_model)
                count = session.exec(statement).one()

                if count > 0:
                    logger.info(f"Database already initialized skipping {database_model}")

                logger.info(f"Initializing database {database_model}")

                templist = []
                for symbol , name in arguments.items():
                    templist.append(database_model(symbol=symbol , name=name))

                session.add_all(templist)
                session.commit()
                logger.info(f"Successfully seeded {len(templist)} records to {database_model}.")


        except Exception as e:
            logger.error(f"An error occurded while initializing database {e}")

    @staticmethod
    def load_initial_stocks(file_path: str) -> dict:
        """
        Fetch initial symbol and name from given json path

        :param file_path: path of relevant json file
        :return: dictionary converted from json
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def initialize_db(file_path: str , database_model: Type[StatBase]):
        """
        orchestrator function for load_initial_stocks and seed_database initializes database model
        :param file_path: path of relevant json file
        :param database_model: relevant table model

        """
        results = StockRepository.load_initial_stocks(file_path=file_path)
        if not results:
            logger.warning(f"Seed data has not been loaded either file_name is missing or empty")
            raise SeedFileNotFoundException

        StockRepository.seed_database(arguments=results, database_model=database_model)












