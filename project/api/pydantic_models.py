from pydantic import BaseModel



class AnalysisModel(BaseModel):
    message: str
    ticker: str | None = None
