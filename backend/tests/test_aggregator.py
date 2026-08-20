from aggregator import _build_suggestions


def _post(post_id, title, score, blobs):
    return {
        "id": post_id,
        "title": title,
        "score": score,
        "permalink": f"https://reddit.com/r/wsb/{post_id}",
        "text_blobs": blobs,
    }


def test_bullish_and_bearish_split():
    posts = [
        _post("1", "GME rocket", 500, ["GME to the moon, diamond hands, printing tendies"]),
        _post("2", "TSLA puts", 200, ["TSLA puts are free money, this stock is crashing"]),
    ]
    result = _build_suggestions(posts)

    bullish_tickers = {t.ticker for t in result.bullish}
    bearish_tickers = {t.ticker for t in result.bearish}

    assert "GME" in bullish_tickers
    assert "TSLA" in bearish_tickers
    assert "GME" not in bearish_tickers
    assert "TSLA" not in bullish_tickers


def test_higher_upvoted_posts_weigh_more_in_average_sentiment():
    posts = [
        _post("1", "bullish big post", 10000, ["AAPL is undervalued, bullish, buying calls"]),
        _post("2", "bearish tiny post", 1, ["AAPL puts, overvalued, crashing"]),
    ]
    result = _build_suggestions(posts)
    aapl = next(t for t in result.all if t.ticker == "AAPL")
    assert aapl.avg_sentiment > 0


def test_mentions_count_across_multiple_blobs_in_same_post():
    posts = [
        _post("1", "GME thread", 100, ["GME is great", "agreed GME to the moon"]),
    ]
    result = _build_suggestions(posts)
    gme = next(t for t in result.all if t.ticker == "GME")
    assert gme.mentions == 2


def test_no_posts_returns_empty_result():
    result = _build_suggestions([])
    assert result.bullish == []
    assert result.bearish == []
    assert result.all == []
