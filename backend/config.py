from pydantic_settings import BaseSettings, SettingsConfigDict

from runtime_paths import ENV_FILE


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    reddit_client_id: str = ""
    reddit_user_agent: str = "wsb-stock-suggestor"

    subreddit: str = "wallstreetbets"
    post_limit: int = 150
    post_listing: str = "hot,rising"
    comments_per_post: int = 15
    cache_ttl_seconds: int = 900


settings = Settings()
