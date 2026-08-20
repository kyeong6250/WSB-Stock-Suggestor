import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from aggregator import get_suggestions
from models import SuggestionsResponse
from reddit_client import RedditFetchError

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="WSB Stock Suggestor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/suggestions", response_model=SuggestionsResponse)
def suggestions(refresh: bool = Query(False, description="Bypass cache and re-fetch from Reddit")):
    try:
        return get_suggestions(force_refresh=refresh)
    except RedditFetchError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/health")
def health():
    return {"status": "ok"}


FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
