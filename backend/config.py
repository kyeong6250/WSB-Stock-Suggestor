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
    post_limit: int = 150
    post_listing: str = "hot,rising"
    comments_per_post: int = 15
    cache_ttl_seconds: int = 900


settings = Settings()
