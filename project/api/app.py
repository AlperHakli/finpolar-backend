from fastapi import FastAPI
from project.api.routes import analysis_route , stocks_route

app = FastAPI()

@app.get("/")
def initialize_api():
    return {"api_message" : "Finpolar api initialized"}


app.include_router(analysis_route.router)
app.include_router(stocks_route.router)

