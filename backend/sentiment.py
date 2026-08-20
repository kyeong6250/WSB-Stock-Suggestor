from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# WSB-specific slang that VADER's general-purpose lexicon doesn't know about.
# Scores follow VADER's convention: roughly -4 (very negative) to +4 (very positive).
WSB_WORD_LEXICON = {
    "bullish": 2.5,
    "bearish": -2.5,
    "moon": 2.5,
    "mooning": 3.0,
    "tendies": 2.0,
    "diamond hands": 2.5,
    "paper hands": -1.5,
    "to the moon": 3.0,
    "yolo": 1.0,
    "printing": 2.0,
    "gains": 2.0,
    "guh": -3.0,
    "bagholder": -2.5,
    "bag holder": -2.5,
    "bagholding": -2.5,
    "rugpull": -3.0,
    "rug pull": -3.0,
    "squeeze": 1.5,
    "short squeeze": 2.5,
    "calls printing": 3.0,
    "puts printing": -3.0,
    "puts": -1.0,
    "calls": 1.0,
    "overvalued": -2.0,
    "undervalued": 2.0,
    "dump": -2.0,
    "dumping": -2.5,
    "pump": 1.5,
    "crashing": -3.0,
    "crash": -2.5,
    "rally": 2.0,
    "rekt": -3.0,
    "loss porn": -2.0,
    "gain porn": 2.5,
    "iv crush": -2.0,
    "dead cat bounce": -1.5,
}

# Emoji sentiment, keyed by the actual glyph for readability here. VADER
# internally rewrites every emoji character to an English description (e.g.
# "🚀" -> "rocket") *before* lexicon lookup, so at load time we translate
# these into entries keyed by that description — see _build_analyzer().
WSB_EMOJI_LEXICON = {
    "🚀": 3.0,
    "🌙": 2.0,
    "💎": 2.0,
    "🙌": 1.5,
    "🐂": 2.0,
    "🐻": -2.0,
    "📉": -2.5,
    "📈": 2.5,
    "🔥": 1.5,
}


def _build_analyzer() -> SentimentIntensityAnalyzer:
    analyzer = SentimentIntensityAnalyzer()
    for emoji, score in WSB_EMOJI_LEXICON.items():
        description = analyzer.emojis.get(emoji)
        if description:
            analyzer.lexicon[description] = score
    analyzer.lexicon.update(WSB_WORD_LEXICON)
    return analyzer


_analyzer = _build_analyzer()


def compound_score(text: str) -> float:
    """Return a compound sentiment score in [-1, 1] for a piece of text."""
    if not text or not text.strip():
        return 0.0
    return _analyzer.polarity_scores(text)["compound"]
