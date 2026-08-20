from sentiment import compound_score


def test_bullish_slang_is_positive():
    assert compound_score("this stock is mooning, diamond hands, printing tendies") > 0.5


def test_bearish_slang_is_negative():
    assert compound_score("bagholding this crashing stock, total rugpull, guh") < -0.5


def test_neutral_text_is_near_zero():
    assert abs(compound_score("the quarterly earnings report is scheduled for tomorrow")) < 0.3


def test_empty_text_is_zero():
    assert compound_score("") == 0.0
    assert compound_score(None) == 0.0


def test_rocket_emoji_is_bullish():
    assert compound_score("GME \U0001F680\U0001F680\U0001F680") > 0
