from pydantic import BaseModel


class SamplePost(BaseModel):
    title: str
    permalink: str
    score: int


class TickerSuggestion(BaseModel):
    ticker: str
    company_name: str
    mentions: int
    avg_sentiment: float
    score: float
    sentiment_label: str
    sample_posts: list[SamplePost]


class FlairCount(BaseModel):
    flair: str
    count: int


class SuggestionsResponse(BaseModel):
    subreddit: str
    generated_at: float
    posts_analyzed: int
    overall_sentiment: float
    high_quality_post_pct: float
    flair_breakdown: list[FlairCount]
    bullish: list[TickerSuggestion]
    bearish: list[TickerSuggestion]
    all: list[TickerSuggestion]
