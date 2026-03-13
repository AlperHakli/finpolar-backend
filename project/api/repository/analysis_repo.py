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
            # print("get_ai_stream async for çalıştı")
            # print(f"DEBUG EVENT: {event['event']}", flush=True)
            # print(f'chunk: {event["data"]}')
            if event["event"] == "on_chat_model_stream":
                # print("on_chat_model_stream")
                content = event["data"]["chunk"].content
                if content:
                    # print("content yield edildi")
                    yield content

