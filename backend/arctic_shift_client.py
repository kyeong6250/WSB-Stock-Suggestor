"""Fetches WSB posts/comments from Arctic Shift (arctic-shift.photon-reddit.com),
an open-source, unauthenticated mirror of Reddit's public data.

Why this exists: Reddit locked self-serve creation of new API apps behind a
manual "Responsible Builder Policy" review in 2026, so PRAW-based fetching
(reddit_client.py) now requires an approval most people won't get. Arctic
Shift needs no API key, no OAuth, no Reddit account at all — it's the default
data source for that reason. See https://github.com/ArthurHeitmann/arctic_shift

Arctic Shift has no "hot"/"rising" concept — it's a plain searchable archive.
We approximate freshness ourselves by pulling everything posted in the last
ARCTIC_SHIFT_WINDOW_HOURS and letting the existing score/flair-weighted
aggregation (aggregator.py) do the ranking, same as it does for PRAW listings.
"""

import logging
import time

import requests

from config import settings
from errors import RedditFetchError

logger = logging.getLogger(__name__)

BASE_URL = "https://arctic-shift.photon-reddit.com"
REQUEST_TIMEOUT = 20

# Arctic Shift is a free, best-effort service with no documented rate limit —
# in practice, firing comment requests back-to-back for every post in a batch
# reliably trips a burst limit (observed as sporadic 422s that succeed again
# seconds later), so a small gap between requests is worth the wall-clock cost.
COMMENT_REQUEST_DELAY_SECONDS = 0.3

# Observed in testing: even a single, isolated request (not part of any burst)
# can come back 422 and then succeed on the very next attempt seconds later —
# so retrying transient-looking failures matters here, not just for bursts.
RETRYABLE_STATUS_CODES = {422, 429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.5

POST_FIELDS = "id,title,selftext,score,num_comments,link_flair_text,created_utc,distinguished"
COMMENT_FIELDS = "id,body,score"

# Arctic Shift doesn't expose a "stickied" flag, so pinned megathreads (which
# would otherwise dominate mention counts) are filtered by these signals
# instead: moderator-distinguished posts, and WSB's recurring megathread titles.
STICKIED_TITLE_HINTS = (
    "daily discussion thread",
    "weekend discussion thread",
    "what are your moves",
)


def _looks_stickied(post: dict) -> bool:
    if post.get("distinguished") == "moderator":
        return True
    title = (post.get("title") or "").strip().lower()
    return any(hint in title for hint in STICKIED_TITLE_HINTS)


def _get(path: str, params: dict, max_attempts: int = MAX_ATTEMPTS) -> list[dict]:
    url = f"{BASE_URL}{path}"
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": settings.reddit_user_agent},
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            status = getattr(exc.response, "status_code", None)
            last_exc = exc
            if attempt < max_attempts and (status is None or status in RETRYABLE_STATUS_CODES):
                logger.info("Arctic Shift request failed (attempt %d/%d, status %s), retrying: %s", attempt, max_attempts, status, url)
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            raise RedditFetchError(
                f"Failed to reach Arctic Shift (Reddit data mirror) at {url}: {exc}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise RedditFetchError(f"Arctic Shift returned a non-JSON response from {url}") from exc

        return payload.get("data", [])

    # Unreachable in practice — the loop above always either returns or raises.
    raise RedditFetchError(f"Failed to reach Arctic Shift (Reddit data mirror) at {url}: {last_exc}")


def _fetch_top_comments(post_id: str, limit: int) -> list[str]:
    if limit <= 0:
        return []
    # Over-fetch and rank client-side by score, since the API only sorts by
    # created_utc — matches how we already pick "top" comments via PRAW.
    # link_id must be a Reddit "fullname" (t3_ prefix) — a bare post id is
    # silently accepted but times out server-side instead of erroring.
    # Only 1 retry (not the default 3): this is already best-effort/optional
    # enrichment across potentially dozens of posts, so a bad run can't
    # compound into minutes of retry backoff — a skipped post still keeps
    # its title/selftext either way.
    comments = _get(
        "/api/comments/search",
        {
            "link_id": f"t3_{post_id}",
            "limit": min(max(limit * 4, 20), 100),
            "fields": COMMENT_FIELDS,
            "sort": "desc",
        },
        max_attempts=2,
    )
    comments.sort(key=lambda c: c.get("score", 0), reverse=True)
    return [c["body"] for c in comments[:limit] if c.get("body")]


def fetch_posts() -> list[dict]:
    """Fetch recent posts (and their top comments) from the configured subreddit."""
    params = {
        "subreddit": settings.subreddit,
        "after": f"{settings.arctic_shift_window_hours}hour",
        "sort": "desc",
        "limit": "auto",
        "fields": POST_FIELDS,
    }

    raw_posts = _get("/api/posts/search", params)

    candidates = [post for post in raw_posts[: settings.post_limit] if not _looks_stickied(post)]

    # Comment-fetching is the expensive part (one HTTP round-trip per post),
    # so it's bounded to the highest-scoring posts rather than done for all
    # of them — every post still contributes its title/selftext regardless.
    comment_eligible_ids = {
        post["id"]
        for post in sorted(candidates, key=lambda p: p.get("score", 0) or 0, reverse=True)[
            : settings.arctic_shift_max_comment_fetches
        ]
    }

    posts = []
    for post in candidates:
        post_id = post["id"]
        text_blobs = [f"{post.get('title', '')}\n{post.get('selftext') or ''}"]

        should_fetch_comments = (
            settings.comments_per_post > 0
            and (post.get("num_comments") or 0) > 0
            and post_id in comment_eligible_ids
        )
        if should_fetch_comments:
            time.sleep(COMMENT_REQUEST_DELAY_SECONDS)
            try:
                text_blobs.extend(_fetch_top_comments(post_id, settings.comments_per_post))
            except RedditFetchError:
                logger.warning("Failed to load comments for post %s", post_id, exc_info=True)

        posts.append(
            {
                "id": post_id,
                "title": post.get("title", ""),
                "score": post.get("score", 0) or 0,
                "num_comments": post.get("num_comments", 0) or 0,
                "flair": post.get("link_flair_text"),
                "permalink": f"https://reddit.com/r/{settings.subreddit}/comments/{post_id}/",
                "created_utc": post.get("created_utc"),
                "text_blobs": text_blobs,
            }
        )

    return posts
