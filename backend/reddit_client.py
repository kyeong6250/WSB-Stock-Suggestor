import logging

import praw
from praw.models import Submission

from config import settings

logger = logging.getLogger(__name__)


class RedditFetchError(RuntimeError):
    pass


def _make_reddit() -> praw.Reddit:
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        raise RedditFetchError(
            "Missing REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET. "
            "Copy .env.example to .env and fill in credentials from "
            "https://www.reddit.com/prefs/apps"
        )
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
        check_for_updates=False,
    )


def _submission_to_dict(submission: Submission, comments_per_post: int) -> dict:
    text_blobs = [f"{submission.title}\n{submission.selftext or ''}"]

    if comments_per_post > 0:
        try:
            submission.comments.replace_more(limit=0)
            top_comments = submission.comments[:comments_per_post]
            for comment in top_comments:
                body = getattr(comment, "body", "")
                if body:
                    text_blobs.append(body)
        except Exception:
            logger.warning("Failed to load comments for post %s", submission.id, exc_info=True)

    return {
        "id": submission.id,
        "title": submission.title,
        "score": submission.score,
        "num_comments": submission.num_comments,
        "permalink": f"https://reddit.com{submission.permalink}",
        "created_utc": submission.created_utc,
        "text_blobs": text_blobs,
    }


def fetch_posts() -> list[dict]:
    """Fetch posts (and their top comments) from the configured subreddit."""
    reddit = _make_reddit()
    subreddit = reddit.subreddit(settings.subreddit)

    listing_fn = {
        "hot": subreddit.hot,
        "new": subreddit.new,
        "top": subreddit.top,
    }.get(settings.post_listing, subreddit.hot)

    posts = []
    try:
        for submission in listing_fn(limit=settings.post_limit):
            if submission.stickied:
                continue
            posts.append(_submission_to_dict(submission, settings.comments_per_post))
    except Exception as exc:
        raise RedditFetchError(f"Failed to fetch posts from r/{settings.subreddit}: {exc}") from exc

    return posts
