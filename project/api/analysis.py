from fastapi import APIRouter, Header

analysis_router = APIRouter(prefix="/analysis", tags=["Stock Analysis"])


@analysis_router.get("/chat")
async def chat_with_agent(prompt: str, llm_api_key=Header(None)):
    ...
