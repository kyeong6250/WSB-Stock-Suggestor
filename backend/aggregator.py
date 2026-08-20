import math
import time
from dataclasses import dataclass, field

from config import settings
from data_source import fetch_posts
from models import FlairCount, SamplePost, SuggestionsResponse, TickerSuggestion
from sentiment import compound_score
from ticker_extractor import company_name, extract_tickers

MAX_SAMPLE_POSTS = 3
FLAIR_BREAKDOWN_TOP_N = 6

# WSB post flairs carry a strong reliability signal: "DD" and similar
# analysis-flaired posts are worth more than upvotes alone suggest, while
# "Meme"/"Shitpost" posts are high-volume noise that shouldn't drive rankings
# as hard as genuine discussion. Unrecognized/missing flairs get 1.0.
FLAIR_WEIGHTS = {
    "dd": 1.4,
    "fundamentals": 1.3,
    "discussion": 1.2,
    "news": 1.2,
    "technical analysis": 1.2,
    "chart": 0.9,
    "yolo": 0.9,
    "gain": 0.8,
    "loss": 0.8,
    "meme": 0.4,
    "shitpost": 0.3,
}

# Flairs treated as genuine analysis rather than noise, used for the
# "high quality post" transparency stat shown in the dashboard.
HIGH_QUALITY_FLAIRS = {"dd", "fundamentals", "discussion", "news", "technical analysis"}


@dataclass
class _TickerStats:
    weight_sum: float = 0.0
    weighted_sentiment_sum: float = 0.0
    mentions: int = 0
    sample_post_ids: set[str] = field(default_factory=set)
    sample_posts: list[SamplePost] = field(default_factory=list)


def _post_weight(post_score: int, flair: str | None) -> float:
    # log-dampen upvotes so a single viral post can't singlehandedly dominate,
    # with a floor so a 0/negative-score post still counts a little.
    weight = math.log10(max(post_score, 0) + 10)
    flair_multiplier = FLAIR_WEIGHTS.get((flair or "").strip().lower(), 1.0)
    return weight * flair_multiplier


def _sentiment_label(score: float) -> str:
    if score > 0.15:
        return "bullish"
    if score < -0.15:
        return "bearish"
    return "neutral"


def _flair_breakdown(posts: list[dict]) -> list[FlairCount]:
    counts: dict[str, int] = {}
    for post in posts:
        flair = (post.get("flair") or "").strip() or "No flair"
        counts[flair] = counts.get(flair, 0) + 1

    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:FLAIR_BREAKDOWN_TOP_N]
    other_count = sum(count for _, count in ranked[FLAIR_BREAKDOWN_TOP_N:])

    result = [FlairCount(flair=flair, count=count) for flair, count in top]
    if other_count:
        result.append(FlairCount(flair="Other", count=other_count))
    return result


def _high_quality_post_pct(posts: list[dict]) -> float:
    if not posts:
        return 0.0
    high_quality = sum(1 for post in posts if (post.get("flair") or "").strip().lower() in HIGH_QUALITY_FLAIRS)
    return round(100 * high_quality / len(posts), 1)


def _build_suggestions(posts: list[dict]) -> SuggestionsResponse:
    stats: dict[str, _TickerStats] = {}

    for post in posts:
        weight = _post_weight(post["score"], post.get("flair"))
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

    total_mentions = sum(t.mentions for t in suggestions)
    overall_sentiment = (
        round(sum(t.avg_sentiment * t.mentions for t in suggestions) / total_mentions, 4)
        if total_mentions
        else 0.0
    )

    return SuggestionsResponse(
        subreddit=settings.subreddit,
        generated_at=time.time(),
        posts_analyzed=len(posts),
        overall_sentiment=overall_sentiment,
        high_quality_post_pct=_high_quality_post_pct(posts),
        flair_breakdown=_flair_breakdown(posts),
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
