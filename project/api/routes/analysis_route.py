from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from project.api.pydantic_models import AnalysisModel
from project.api.repository.analysis_repo import AnalysisRepo
import json
router = APIRouter(prefix="/analysis" ,tags=["Stock Analysis"])

@router.post("/chat")
async def chat_llm(request: AnalysisModel):
    async def sse_wrapper():

        async for token in AnalysisRepo.get_ai_stream(request.message , session_id= request.session_id):

            data = json.dumps({"text": token} , ensure_ascii=False)
            yield f"data: {data}\n\n"

    return StreamingResponse(sse_wrapper(), media_type="text/event-stream")
