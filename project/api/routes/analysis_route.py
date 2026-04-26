import asyncio

from fastapi import APIRouter , Request
from fastapi.responses import StreamingResponse
from project.api.base_models import AnalysisModel
from project.api.repository.analysis_repo import AnalysisRepo
from slowapi import Limiter
from slowapi.util import get_remote_address
import json
router = APIRouter(prefix="/analysis" ,tags=["AI chat"])


limiter = Limiter(key_func=get_remote_address)

@router.post("/chat")
@limiter.limit("5/day")
async def chat_llm(request: Request, analysis_data: AnalysisModel):
    async def sse_wrapper():
        async for token in AnalysisRepo.get_ai_stream(analysis_data.message, session_id=analysis_data.session_id):
            data = json.dumps({"text": token}, ensure_ascii=False)
            print(f"Returned data: {data}", flush=True)
            yield f"data: {data}\n\n"

    return StreamingResponse(
        sse_wrapper(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/test-stream")
async def test_stream():
    async def simple_gen():
        for i in range(10):
            yield f"data: Token {i}\n\n"
            await asyncio.sleep(0.5)
    return StreamingResponse(simple_gen(), media_type="text/event-stream")
