import redis.asyncio as redis
from settings import  settings
class RedisClient():
    def __init__(self , redis_port: int , redis_host: str):
        self.redis_port = redis_port
        self.redis_host = redis_host
        self.redis_client = None

    async def connect(self):
        self.redis_client = redis.Redis(
            decode_responses=True,
            port=self.redis_port,
            host=self.redis_host
        )
    async def setIndicatorDict(self ,name:str ,  value: dict , exp:int = 300):
        await self.redis_client.set(name= name , value=value , ex = exp)

    async def getIndicatorDict(self , name:str):
        await self.redis_client.get(name)

redis_manager = RedisClient(redis_host= settings.REDIS_HOST , redis_port= settings.REDIS_PORT)

