from fastapi import FastAPI

from app.api.routes.quotes import router as quotes_router

app = FastAPI()
app.include_router(quotes_router)


@app.get("/health")
def health():
    return {"status": "ok"}