from pydantic_settings import BaseSettings, SettingsConfigDict

from runtime_paths import ENV_FILE


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    # "arctic_shift" needs no setup at all (default); "praw" uses the official
    # Reddit API and needs reddit_client_id, for anyone who already has (or can
    # get past Reddit's 2026 manual app-approval process to get) API access.
    data_source: str = "arctic_shift"
    arctic_shift_window_hours: int = 24
    # Each post needing comments costs its own HTTP round-trip (Arctic Shift
    # has no "give me comments for these 100 posts in one call" endpoint), so
    # fetching comments for every one of post_limit posts doesn't scale —
    # with defaults that's 2+ minutes on a first load. Cap it to the
    # highest-scoring posts, where comment context matters most anyway.
    arctic_shift_max_comment_fetches: int = 40

    reddit_client_id: str = ""
    reddit_user_agent: str = "wsb-stock-suggestor"

    subreddit: str = "wallstreetbets"
    # Generous enough that it rarely truncates what's actually available in
    # arctic_shift_window_hours (typically ~150-250 posts/day for WSB) rather
    # than acting as a real cap.
    post_limit: int = 300
    post_listing: str = "hot,rising"
    comments_per_post: int = 15
    # Ceiling on how stale served data is allowed to get before a request is
    # forced to block on a synchronous refetch. In practice this is rarely
    # hit — background_refresh_interval_seconds keeps the cache warm well
    # under this — it's a fallback, not the primary freshness mechanism.
    cache_ttl_seconds: int = 86400
    # How often to proactively refresh in the background (independent of any
    # request), so: (a) visitors almost always hit an already-warm cache
    # instead of occasionally eating a ~15s synchronous fetch, and (b) the
    # sentiment-history sparkline actually accumulates points over time
    # rather than only advancing when a cache miss happens to occur.
    background_refresh_interval_seconds: int = 1800
    sentiment_history_max_points: int = 50


settings = Settings()
