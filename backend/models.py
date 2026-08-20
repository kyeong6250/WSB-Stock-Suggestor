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


class SuggestionsResponse(BaseModel):
    subreddit: str
    generated_at: float
    posts_analyzed: int
    bullish: list[TickerSuggestion]
    bearish: list[TickerSuggestion]
    all: list[TickerSuggestion]
