"""FastAPI application entry point.

TODO:
- Create the FastAPI application and configure metadata.
- Register the versioned API router and CORS middleware.
- Start and stop database and scheduler resources in lifespan hooks.
- Add clean exception handlers without placing business logic here.
"""
from fastapi import FastAPI

from app.core.config import settings
from app.db.session import check_database_connection


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "message": "Family Context Agent API is running"
    }


@app.get("/health")
async def health():
    database_ok = await check_database_connection()

    return {
        "status": "ok",
        "database": "connected" if database_ok else "disconnected",
    }