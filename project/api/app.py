from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from project.api.routes import analysis_route , stocks_route

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def initialize_api():
    return {"api_message" : "Finpolar api initialized"}



app.include_router(analysis_route.router)
app.include_router(stocks_route.router)

