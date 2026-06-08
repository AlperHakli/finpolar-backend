import json
import logging
from typing import Any

import redis.asyncio as redis
from settings import  settings

logger = logging.getLogger(__name__)

class RedisClient():
    def __init__(self , redis_port: int , redis_host: str):
        self.redis_port = redis_port
        self.redis_host = redis_host
        self.redis_client = None

    async def connect(self):
        if self.redis_client is None:
            self.redis_client = redis.Redis(
                decode_responses=True,
                port=self.redis_port,
                host=self.redis_host
            )
            logger.info("Connected to Redis successfully")

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    async def setRedis(self, name:str, value: dict, exp:int = 300):
        """
        Writes dictionary data to redis
        """
        json_value = json.dumps(value)
        await self.redis_client.set(name= name , value=json_value , ex = exp)

    async def setRedisNoDict(self, name:str, value: Any, exp:int = 300):
        """
        Writes data to redis
        """

        await self.redis_client.set(name= name , value=value , ex = exp)

    async def setRedisNoExp(self, name:str, value: dict):
        """
        Writes data to redis without an expiration date
        """
        await self.connect()  # Connect if connection does not exist
        json_value = json.dumps(value)
        await self.redis_client.set(name= name , value=json_value)


    async def getRedis(self, name:str):
        await self.connect()

        value = await self.redis_client.get(name)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

redis_manager = RedisClient(redis_host= settings.REDIS_HOST , redis_port= settings.REDIS_PORT)

