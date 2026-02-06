from project.ai.maingraph import app

class AnalysisRepo():
    @staticmethod
    async def get_ai_stream(user_message: str , session_id: str):

        config = {"configurable": {"thread_id": session_id}}

        async for event in app.astream_events(
            input={"messages" : [("user" , user_message)]},
            version="v2",
            config=config
        ):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content

