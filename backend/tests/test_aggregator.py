from aggregator import _build_suggestions, _post_weight


def _post(post_id, title, score, blobs, flair=None):
    return {
        "id": post_id,
        "title": title,
        "score": score,
        "flair": flair,
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
    assert result.overall_sentiment == 0.0
    assert result.high_quality_post_pct == 0.0
    assert result.flair_breakdown == []


def test_overall_sentiment_is_mentions_weighted():
    posts = [
        _post("1", "very bullish, mentioned a lot", 500, ["GME undervalued bullish"] * 3),
        _post("2", "slightly bearish, mentioned once", 500, ["TSLA slightly overvalued"]),
    ]
    result = _build_suggestions(posts)
    # GME has 3x the mentions of TSLA and is more strongly positive, so the
    # mentions-weighted overall sentiment should skew positive.
    assert result.overall_sentiment > 0


def test_flair_breakdown_counts_posts_by_flair_with_no_flair_bucket():
    posts = [
        _post("1", "a", 10, ["AAPL"], flair="DD"),
        _post("2", "b", 10, ["AAPL"], flair="DD"),
        _post("3", "c", 10, ["AAPL"], flair="Meme"),
        _post("4", "d", 10, ["AAPL"], flair=None),
    ]
    result = _build_suggestions(posts)
    breakdown = {fc.flair: fc.count for fc in result.flair_breakdown}
    assert breakdown["DD"] == 2
    assert breakdown["Meme"] == 1
    assert breakdown["No flair"] == 1


def test_high_quality_post_pct():
    posts = [
        _post("1", "a", 10, ["AAPL"], flair="DD"),
        _post("2", "b", 10, ["AAPL"], flair="Discussion"),
        _post("3", "c", 10, ["AAPL"], flair="Meme"),
        _post("4", "d", 10, ["AAPL"], flair="Meme"),
    ]
    result = _build_suggestions(posts)
    assert result.high_quality_post_pct == 50.0


def test_dd_flair_weighs_more_than_meme_flair():
    dd_weight = _post_weight(100, "DD")
    meme_weight = _post_weight(100, "Meme")
    plain_weight = _post_weight(100, None)
    assert dd_weight > plain_weight > meme_weight


def test_flair_is_case_insensitive():
    assert _post_weight(100, "dd") == _post_weight(100, "DD")


def test_meme_flaired_post_pulls_score_toward_its_sentiment_less():
    posts_with_meme = [
        _post("1", "big bullish DD", 500, ["AAPL undervalued, bullish, buying calls"], flair="DD"),
        _post("2", "meme dump", 500, ["AAPL puts, overvalued, crashing"], flair="Meme"),
    ]
    result = _build_suggestions(posts_with_meme)
    aapl = next(t for t in result.all if t.ticker == "AAPL")
    assert aapl.avg_sentiment > 0
