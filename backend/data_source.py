"""Picks which backend fetches Reddit posts, based on DATA_SOURCE in .env.

- "arctic_shift" (default): no setup required, see arctic_shift_client.py
- "praw": the official Reddit API, for anyone who already has (or can get)
  an approved Reddit API app; see reddit_client.py
"""

from config import settings


def fetch_posts() -> list[dict]:
    if settings.data_source == "praw":
        from reddit_client import fetch_posts as _fetch_posts
    else:
        from arctic_shift_client import fetch_posts as _fetch_posts
    return _fetch_posts()
