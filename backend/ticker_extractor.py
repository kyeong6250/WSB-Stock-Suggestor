import csv
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# Words/acronyms that are technically valid tickers but are overwhelmingly used
# as regular English words or WSB slang in this context. Filtered out unless
# written as a cashtag (e.g. $IT), which signals real intent.
BLOCKLIST = {
    "A", "I", "ALL", "AM", "AN", "AND", "ARE", "AS", "AT", "BE", "BIG", "BY",
    "CEO", "CFO", "COO", "DD", "DID", "DO", "EOD", "EPS", "ETF", "EV", "FOR",
    "FUD", "FOMO", "GDP", "GG", "GO", "GOOD", "HAS", "HAVE", "HERE", "HODL",
    "HOLD", "IMO", "IPO", "IRA", "IS", "ITM", "IT", "JUST", "LFG", "LMAO",
    "LOL", "LOVE", "ME", "MOASS", "MOON", "NEW", "NEWS", "NOW", "OF", "OK",
    "ON", "ONE", "OPEN", "OR", "OTM", "PLAY", "PM", "PT", "PUMP", "PUT",
    "PUTS", "CALL", "CALLS", "RH", "RIP", "SEC", "SO", "TOS", "THE", "TO",
    "TOP", "UP", "US", "USA", "USD", "WSB", "WTF", "YOLO", "YOU", "YOLOED",
    "ATH", "ATL", "AF", "OG", "ER", "Q1", "Q2", "Q3", "Q4", "CEO'S", "FYI",
    "AKA", "ASAP", "DM", "EDIT", "FAQ", "GAIN", "GAINS", "LOSS", "LOSSES",
    "REAL", "TA", "FA", "IV", "OI", "B", "K", "M",
}

_CASHTAG_RE = re.compile(r"\$([A-Za-z]{1,5})\b")
_BARE_RE = re.compile(r"\b([A-Z]{2,5})\b")


def _load_tickers(*filenames: str) -> dict[str, str]:
    tickers: dict[str, str] = {}
    for filename in filenames:
        path = DATA_DIR / filename
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                symbol = row["Symbol"].strip().upper().replace(".", "-")
                name = row.get("Security", "").strip()
                if symbol and symbol not in tickers:
                    tickers[symbol] = name
    return tickers


# Trusted set (S&P 500 + hand-picked WSB favorites) used for *bare* uppercase
# word matching, e.g. "GME to the moon" — kept small and curated because bare
# words carry no explicit signal, so a bigger universe here just means more
# false positives from ordinary all-caps chatter.
KNOWN_TICKERS: dict[str, str] = _load_tickers("sp500.csv", "extra_tickers.csv")

# Full NASDAQ/NYSE/AMEX common-stock universe (~5,700 symbols), used only for
# explicit "$TICKER" cashtags — the "$" is unambiguous intent, so it's safe to
# recognize small/micro-cap tickers here that aren't in the trusted set above.
ALL_TICKERS: dict[str, str] = {**_load_tickers("all_tickers.csv"), **KNOWN_TICKERS}


def company_name(ticker: str) -> str:
    return ALL_TICKERS.get(ticker, ticker)


def extract_tickers(text: str) -> set[str]:
    """Return the set of valid ticker symbols mentioned in a piece of text."""
    if not text:
        return set()

    found: set[str] = set()

    for match in _CASHTAG_RE.finditer(text):
        symbol = match.group(1).upper()
        if symbol in ALL_TICKERS:
            found.add(symbol)

    for match in _BARE_RE.finditer(text):
        symbol = match.group(1)
        if symbol in KNOWN_TICKERS and symbol not in BLOCKLIST:
            found.add(symbol)

    return found
