import math
import time
from dataclasses import dataclass, field

from config import settings
from models import SamplePost, SuggestionsResponse, TickerSuggestion
from reddit_client import fetch_posts
from sentiment import compound_score
from ticker_extractor import company_name, extract_tickers

MAX_SAMPLE_POSTS = 3


@dataclass
class _TickerStats:
    weight_sum: float = 0.0
    weighted_sentiment_sum: float = 0.0
    mentions: int = 0
    sample_post_ids: set[str] = field(default_factory=set)
    sample_posts: list[SamplePost] = field(default_factory=list)


def _post_weight(post_score: int) -> float:
    # log-dampen upvotes so a single viral post can't singlehandedly dominate,
    # with a floor so a 0/negative-score post still counts a little.
    return math.log10(max(post_score, 0) + 10)


def _sentiment_label(score: float) -> str:
    if score > 0.15:
        return "bullish"
    if score < -0.15:
        return "bearish"
    return "neutral"


def _build_suggestions(posts: list[dict]) -> SuggestionsResponse:
    stats: dict[str, _TickerStats] = {}

    for post in posts:
        weight = _post_weight(post["score"])
        for blob in post["text_blobs"]:
            tickers = extract_tickers(blob)
            if not tickers:
                continue
            sentiment = compound_score(blob)
            for ticker in tickers:
                s = stats.setdefault(ticker, _TickerStats())
                s.weight_sum += weight
                s.weighted_sentiment_sum += sentiment * weight
                s.mentions += 1
                if post["id"] not in s.sample_post_ids and len(s.sample_posts) < MAX_SAMPLE_POSTS:
                    s.sample_post_ids.add(post["id"])
                    s.sample_posts.append(
                        SamplePost(title=post["title"], permalink=post["permalink"], score=post["score"])
                    )

    suggestions: list[TickerSuggestion] = []
    for ticker, s in stats.items():
        avg_sentiment = s.weighted_sentiment_sum / s.weight_sum if s.weight_sum else 0.0
        composite_score = avg_sentiment * math.log2(s.mentions + 1)
        suggestions.append(
            TickerSuggestion(
                ticker=ticker,
                company_name=company_name(ticker),
                mentions=s.mentions,
                avg_sentiment=round(avg_sentiment, 4),
                score=round(composite_score, 4),
                sentiment_label=_sentiment_label(avg_sentiment),
                sample_posts=sorted(s.sample_posts, key=lambda p: p.score, reverse=True),
            )
        )

    all_sorted = sorted(suggestions, key=lambda t: t.mentions, reverse=True)
    bullish = sorted(
        [t for t in suggestions if t.score > 0], key=lambda t: t.score, reverse=True
    )
    bearish = sorted([t for t in suggestions if t.score < 0], key=lambda t: t.score)

    return SuggestionsResponse(
        subreddit=settings.subreddit,
        generated_at=time.time(),
        posts_analyzed=len(posts),
        bullish=bullish[:25],
        bearish=bearish[:25],
        all=all_sorted[:100],
    )


_cache: SuggestionsResponse | None = None
_cache_time: float = 0.0


def get_suggestions(force_refresh: bool = False) -> SuggestionsResponse:
    global _cache, _cache_time

    now = time.time()
    if not force_refresh and _cache is not None and (now - _cache_time) < settings.cache_ttl_seconds:
        return _cache

    posts = fetch_posts()
    result = _build_suggestions(posts)

    _cache = result
    _cache_time = now
    return result
