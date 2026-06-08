import logging

from project.ai.maingraph import app
from project.ai.aisummarygraph import summary_app
from project.api.redis_client import RedisClient
from settings import settings
logger = logging.getLogger(__name__)
class AnalysisRepo():


    @staticmethod
    async def get_ai_stream(user_message: str , session_id: str):

        config = {"configurable": {"thread_id": session_id}}


        async for event in app.astream_events(
            input={"messages" : [("user" , user_message)]},
            version="v2",
            config=config
        ):
            # print("get_ai_stream async for çalıştı")
            # print(f"DEBUG EVENT: {event['event']}", flush=True)
            # print(f'chunk: {event["data"]}')
            if event["event"] == "on_chat_model_stream":
                # print("on_chat_model_stream")
                content = event["data"]["chunk"].content
                if content:
                    # print("content yield edildi")
                    yield content



    @staticmethod
    async def get_summary_score(symbol: str , session_id: str ,   redis_manager: RedisClient):
        """returns score of given symbol between 1 and 100 (more close the 100 means better opportunity to buy)
        session_id: current id of memory session frontend will provide this


        """
        try:
            symbolupper = symbol.upper()

            # did not find better way than hardcoding this prompt
            SUMMARY_AGENT_USER_PROMPT = f"""
            Analyze given ticker with all tools that you have got and response all analyses like professional finance advisor
            ticker symbol : {symbolupper}
            """

            #cache control
            key = f"{symbolupper}:{"ai_score"}"
            cache = await redis_manager.getRedis(name=key)
            if cache is None:
                logger.info(f"Cache miss on ai summary calculating asset score with given symbol: {symbolupper}")
                response = await summary_app.ainvoke(input={"messages": [("user", SUMMARY_AGENT_USER_PROMPT)]} , config={"configurable": {"thread_id":session_id}})
                last_message = response["messages"][-1]
                answer = int(last_message.content)
                await redis_manager.setRedisNoDict(name=key , value=answer , exp=settings.AI_SUMMARY_REDIS_DURATION)
                return {"ai_score" : answer}
            return {"ai_score" : cache}


        except Exception as e:
            print(f"Exception when summary {e}")
            return 50








