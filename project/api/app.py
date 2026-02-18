from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from project.api.routes.analysis_route import limiter
from project.api.routes import analysis_route , stocks_route

app = FastAPI()

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def initialize_api():
    return {"api_message" : "Finpolar api initialized"}



app.include_router(analysis_route.router)
app.include_router(stocks_route.router)

