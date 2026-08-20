# WSB Stock Suggestor

Ranks stock tickers by mention frequency and sentiment across recent posts and
comments on [r/wallstreetbets](https://www.reddit.com/r/wallstreetbets/),
presented as a simple bullish/bearish dashboard.

**This is not a price predictor and not financial advice.** It's a transparent
sentiment + buzz ranking: how often a ticker is mentioned, and whether the
surrounding language (including WSB-specific slang and emoji) reads positive
or negative. WSB sentiment is famously unreliable and often ironic — treat
this as an entertaining lens on retail chatter, not a trading signal.

## How it works

1. **Fetch** — pulls the top posts (and their top comments) from r/wallstreetbets via the official Reddit API (PRAW), including each post's flair (DD, Meme, YOLO, etc.).
2. **Extract tickers** — two tiers, to balance recall against false positives:
   - **Bare uppercase words** ("GME to the moon") are only matched against a curated, trusted list (S&P 500 + hand-picked WSB favorites) and filtered against a blocklist of common English words/acronyms that collide with real tickers (e.g. `DD`, `YOLO`, `IT`, `ALL`).
   - **`$TICKER` cashtags** are explicit intent, so they're checked against the full ~5,700-symbol NASDAQ/NYSE/AMEX common-stock universe — this is what catches small/micro-caps outside the trusted list.
3. **Score sentiment** — runs VADER sentiment analysis, extended with a WSB slang/emoji lexicon (🚀, 💎🙌, "bagholder", "tendies", "diamond hands", etc.).
4. **Aggregate** — combines mention count and a weighted average sentiment per ticker into a single score, ranked into Bullish / Bearish / All tabs. Weighting favors higher-upvoted posts (log-dampened) and analysis-flaired posts ("DD", "Discussion", "Fundamentals"), while down-weighting high-noise flairs ("Meme", "Shitpost").
5. Results are cached for `CACHE_TTL_SECONDS` (default 15 min) to stay within Reddit API rate limits.

## Setup

### 1. Create a Reddit API app

Only one value is needed — no client secret, no login flow at runtime. This
uses Reddit's "installed app" OAuth type, which is a public/non-confidential
client meant to run unattended in read-only mode.

1. Go to <https://www.reddit.com/prefs/apps> (log into your Reddit account first).
2. Click **create app** / **create another app** at the bottom.
3. Choose type **installed app** (not "script" — that type requires a secret).
4. Name: anything (e.g. `wsb-stock-suggestor`). Redirect URI: `http://localhost:8080` (required by the form, unused by this app).
5. Click **create app**, then copy the string shown under the app's name — that's the client ID.

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_USER_AGENT=wsb-stock-suggestor by u/your_reddit_username
```

### 3. Install & run

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

Open <http://localhost:8000> in your browser.

## Desktop app (Windows .exe)

The same dashboard also runs as a native Windows desktop app — a proper
window with no browser chrome, launched by double-clicking an .exe — instead
of a browser tab. It's the same FastAPI backend, just opened inside a native
window via [pywebview](https://pywebview.flowrl.com/) instead of a browser.

**Build it yourself:**

```bash
pip install -r requirements-desktop.txt
python build_exe.py
```

This produces `dist/WSB-Stock-Suggestor.exe` (a single-file executable — no
Python install required to run it).

**First launch:** since the exe has no credentials baked in, it opens the
Reddit apps page in your browser and pops up a single prompt asking you to
paste a client ID (see [Setup](#setup) above for how to get one — it only
takes copying one string, no secret). Paste it, hit OK, and the dashboard
opens immediately — no relaunch needed. The `.env` it writes next to the exe
persists between launches, so this only happens once.

## API

- `GET /api/suggestions` — cached ranked suggestions (bullish/bearish/all).
- `GET /api/suggestions?refresh=true` — bypass cache, re-fetch from Reddit.
- `GET /api/health` — liveness check.

## Project structure

```
backend/
  main.py              FastAPI app, serves API + static frontend
  config.py            Env-driven settings
  runtime_paths.py     Path resolution that works both from source and inside the packaged .exe
  reddit_client.py     PRAW wrapper: fetch posts + top comments
  ticker_extractor.py  Cashtag/ticker regex extraction + known-ticker validation
  sentiment.py          VADER + WSB slang/emoji lexicon
  aggregator.py         Combines mentions + sentiment into ranked scores, caches results
  models.py             Pydantic response models
  desktop.py             Desktop entry point (pywebview window + first-run .env setup)
  data/                 S&P 500 + WSB-favorites (trusted) and full-market (cashtag-only) ticker lists
frontend/
  index.html / style.css / app.js   Static dashboard (no build step)
assets/
  icon.ico             App icon, generated by scripts/generate_icon.py
build_exe.py           PyInstaller build script for the desktop .exe
```

## Tuning

Edit `.env`:

- `SUBREDDIT` — analyze a different subreddit.
- `POST_LISTING` — `hot`, `new`, `top`, or `rising`. Comma-separate several (e.g. `hot,rising`, the default) to merge them, deduplicated — `hot` alone skews toward posts that have been popular for a while, so mixing in `rising` keeps the ranking from leaning entirely on stale threads.
- `POST_LIMIT` — how many posts to pull per refresh, per listing.
- `COMMENTS_PER_POST` — how many top-level comments to analyze per post (0 = titles/selftext only, faster).
- `CACHE_TTL_SECONDS` — how long results are cached before re-fetching.

## Disclaimer

Built for educational and portfolio purposes. Nothing in this project is
investment advice. Reddit sentiment is not a reliable predictor of stock
price movement — always do your own research before making financial
decisions.
