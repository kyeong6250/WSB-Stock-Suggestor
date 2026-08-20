import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from aggregator import get_suggestions
from errors import RedditFetchError
from models import SuggestionsResponse
from runtime_paths import FRONTEND_DIR

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="WSB Stock Suggestor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_store_cache_control(request, call_next):
    # Hosts like Render sit behind a CDN (Cloudflare) that can cache a
    # response from a single unlucky request — e.g. a 404 hit during the
    # container's first few seconds of cold-start — and then keep serving
    # that stale response to every subsequent visitor indefinitely. This is
    # a small app with no real caching upside, so it's simplest to just tell
    # every intermediary never to cache anything, for every path.
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/suggestions", response_model=SuggestionsResponse)
def suggestions(refresh: bool = Query(False, description="Bypass cache and re-fetch from Reddit")):
    try:
        return get_suggestions(force_refresh=refresh)
    except RedditFetchError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/health")
def health():
    return {"status": "ok"}


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
