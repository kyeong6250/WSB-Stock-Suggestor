from fastapi.testclient import TestClient

import aggregator
from main import app

client = TestClient(app)


def _fake_posts():
    return [
        {
            "id": "1",
            "title": "GME to the moon",
            "score": 500,
            "permalink": "https://reddit.com/r/wsb/1",
            "text_blobs": ["GME to the moon, diamond hands, printing tendies"],
        },
        {
            "id": "2",
            "title": "TSLA puts",
            "score": 200,
            "permalink": "https://reddit.com/r/wsb/2",
            "text_blobs": ["TSLA puts are free money, this stock is crashing"],
        },
    ]


def setup_function():
    aggregator._cache = None
    aggregator._cache_time = 0.0
    aggregator._history = []


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_frontend_is_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "WSB Stock Suggestor" in res.text


def test_responses_are_never_cached_by_an_intermediary():
    # A CDN in front of this app (e.g. Render's) can cache a bad response
    # from a single cold-start request and serve it to every visitor after
    # — every response must explicitly forbid that, static assets included.
    for path in ["/api/health", "/", "/style.css", "/app.js"]:
        res = client.get(path)
        assert res.headers.get("cache-control") == "no-store", path


def test_suggestions_without_credentials_returns_503(monkeypatch):
    from reddit_client import RedditFetchError

    def raise_fetch_error():
        raise RedditFetchError("Missing REDDIT_CLIENT_ID")

    monkeypatch.setattr(aggregator, "fetch_posts", raise_fetch_error)

    res = client.get("/api/suggestions")
    assert res.status_code == 503
    assert "REDDIT_CLIENT_ID" in res.json()["detail"]


def test_suggestions_success(monkeypatch):
    monkeypatch.setattr(aggregator, "fetch_posts", _fake_posts)

    res = client.get("/api/suggestions")
    assert res.status_code == 200
    body = res.json()

    assert body["posts_analyzed"] == 2
    bullish_tickers = {t["ticker"] for t in body["bullish"]}
    bearish_tickers = {t["ticker"] for t in body["bearish"]}
    assert "GME" in bullish_tickers
    assert "TSLA" in bearish_tickers
