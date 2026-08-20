from ticker_extractor import extract_tickers


def test_extracts_bare_known_tickers():
    assert extract_tickers("I love GME and AMC") == {"GME", "AMC"}


def test_extracts_cashtags():
    assert extract_tickers("buying $TSLA calls") == {"TSLA"}


def test_filters_common_words_that_collide_with_tickers():
    text = "DD: YOLO all in, IT is a great company (should not trigger), ALL good"
    assert extract_tickers(text) == set()


def test_unknown_uppercase_words_are_ignored():
    assert extract_tickers("LOOK AT THIS RANDOM ACRONYM XQZVK") == set()


def test_cashtag_still_filtered_if_not_a_known_ticker():
    assert extract_tickers("$ZZZZZ is not a real ticker") == set()


def test_empty_text():
    assert extract_tickers("") == set()
    assert extract_tickers(None) == set()


def test_multiple_tickers_in_one_blob():
    assert extract_tickers("DD on AAPL and NVDA, both undervalued") == {"AAPL", "NVDA"}
