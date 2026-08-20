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


def _load_known_tickers() -> dict[str, str]:
    tickers: dict[str, str] = {}
    for filename in ("sp500.csv", "extra_tickers.csv"):
        path = DATA_DIR / filename
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                symbol = row["Symbol"].strip().upper().replace(".", "-")
                name = row.get("Security", "").strip()
                if symbol and symbol not in tickers:
                    tickers[symbol] = name
    return tickers


KNOWN_TICKERS: dict[str, str] = _load_known_tickers()


def company_name(ticker: str) -> str:
    return KNOWN_TICKERS.get(ticker, ticker)


def extract_tickers(text: str) -> set[str]:
    """Return the set of valid ticker symbols mentioned in a piece of text."""
    if not text:
        return set()

    found: set[str] = set()

    for match in _CASHTAG_RE.finditer(text):
        symbol = match.group(1).upper()
        if symbol in KNOWN_TICKERS:
            found.add(symbol)

    for match in _BARE_RE.finditer(text):
        symbol = match.group(1)
        if symbol in KNOWN_TICKERS and symbol not in BLOCKLIST:
            found.add(symbol)

    return found
