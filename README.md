# WSB Stock Suggestor

Ranks stock tickers by mention frequency and sentiment across recent posts and
comments on [r/wallstreetbets](https://www.reddit.com/r/wallstreetbets/),
presented as a simple bullish/bearish dashboard.

**This is not a price predictor and not financial advice.** It's a transparent
sentiment + buzz ranking: how often a ticker is mentioned, and whether the
surrounding language (including WSB-specific slang and emoji) reads positive
or negative. WSB sentiment is famously unreliable and often ironic — treat
this as an entertaining lens on retail chatter, not a trading signal.

**Needs zero setup by default** — no Reddit account, no API key, no login.
See [Data sources](#data-sources) for why and how.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/kyeong6250/WSB-Stock-Suggestor)

## How it works

1. **Fetch** — pulls recent posts (and their top comments) from r/wallstreetbets, including each post's flair (DD, Meme, YOLO, etc.). See [Data sources](#data-sources) for where this data actually comes from.
2. **Extract tickers** — two tiers, to balance recall against false positives:
   - **Bare uppercase words** ("GME to the moon") are only matched against a curated, trusted list (S&P 500 + hand-picked WSB favorites) and filtered against a blocklist of common English words/acronyms that collide with real tickers (e.g. `DD`, `YOLO`, `IT`, `ALL`).
   - **`$TICKER` cashtags** are explicit intent, so they're checked against the full ~5,700-symbol NASDAQ/NYSE/AMEX common-stock universe — this is what catches small/micro-caps outside the trusted list.
3. **Score sentiment** — runs VADER sentiment analysis, extended with a WSB slang/emoji lexicon (🚀, 💎🙌, "bagholder", "tendies", "diamond hands", etc.).
4. **Aggregate** — combines mention count and a weighted average sentiment per ticker into a single score, ranked into Bullish / Bearish / All tabs. Weighting favors higher-upvoted posts (log-dampened) and analysis-flaired posts ("DD", "Discussion", "Fundamentals"), while down-weighting high-noise flairs ("Meme", "Shitpost").
5. Results are cached for `CACHE_TTL_SECONDS` (default 15 min).

## Data sources

Reddit locked self-serve creation of new API apps behind a manual
"Responsible Builder Policy" review sometime in late 2025/2026 — trying to
create one now often just fails outright (see
[this thread](https://www.reddit.com/r/redditdev/comments/1qpjqw2/unable_to_create_app_error_read_builder_policy/)).
So this project defaults to a source that sidesteps that entirely:

- **`arctic_shift` (default, zero setup)** — [Arctic Shift](https://github.com/ArthurHeitmann/arctic_shift) is an open-source, unauthenticated mirror of Reddit's public data. No API key, no login, no registration. It has no "hot"/"rising" concept of its own, so this app pulls everything posted in the last `ARCTIC_SHIFT_WINDOW_HOURS` (default 24) and does its own score/flair-weighted ranking on top, same as it would with a live listing. It's a free, best-effort third-party service with no uptime guarantee — reliable enough for this, but not something to depend on for anything critical.
- **`praw` (opt-in)** — the official Reddit API, for anyone who already has an approved app, or gets through Reddit's review process. Set `DATA_SOURCE=praw` in `.env` and provide a client ID (see below) — the desktop app will prompt for it automatically.

### Using `praw` instead

Only one value is needed — no client secret, no login flow at runtime. This
uses Reddit's "installed app" OAuth type, which is a public/non-confidential
client meant to run unattended in read-only mode.

1. Go to <https://www.reddit.com/prefs/apps> (log into your Reddit account first).
2. Click **create app** / **create another app** at the bottom.
3. Choose type **installed app** (not "script" — that type requires a secret).
4. Name: anything (e.g. `wsb-stock-suggestor`). Redirect URI: `http://localhost:8080` (required by the form, unused by this app).
5. Click **create app**, then copy the string shown under the app's name — that's the client ID.
6. In `.env`, set `DATA_SOURCE=praw` and `REDDIT_CLIENT_ID=your_client_id`.

## Install & run

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

Open <http://localhost:8000> in your browser — no `.env` needed at all for the default data source.

## Deploy (live web version)

The .exe below is Windows-only and, being an unsigned executable, triggers a
SmartScreen warning for anyone downloading it — not something to hand a
stranger a link to. The web version has neither problem: it's just a page.

Click the badge above ("Deploy to Render"), or manually:

1. Fork or use this repo directly.
2. On [Render](https://render.com), **New +** → **Blueprint** → connect this repo. Render reads [`render.yaml`](render.yaml) and sets everything up automatically (free tier, no credit card).
3. Deploy. You'll get a public URL like `https://wsb-stock-suggestor.onrender.com`.

Render's free tier spins the service down after 15 minutes of no traffic, and
the first request after that can race the container's startup — Render's own
edge sometimes returns a bare 404 for a request that lands before the app is
actually listening (distinguishable by an `x-render-routing: no-server`
response header; the request landing a moment later succeeds). [`.github/workflows/keep-alive.yml`](.github/workflows/keep-alive.yml)
pings the service every 10 minutes to keep it always warm and sidestep this
entirely — it only runs once you've deployed your own instance and pushed to
your fork (GitHub Actions can't ping a URL that doesn't exist yet), and
GitHub auto-disables scheduled workflows after 60 days with no commits to
the repo, so an idle fork will eventually need a push (or `workflow_dispatch`
from the Actions tab) to re-enable it.

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

**First launch:** with the default data source, nothing to set up — just
double-click it. If you've opted into `DATA_SOURCE=praw` via `.env` without a
client ID yet, it'll instead open the Reddit apps page in your browser and
prompt for one (see [Data sources](#data-sources)); paste it and the
dashboard opens immediately, no relaunch needed.

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
  data_source.py        Picks arctic_shift_client or reddit_client based on DATA_SOURCE
  arctic_shift_client.py  Default fetcher: no-auth Arctic Shift mirror (see Data sources)
  reddit_client.py     Opt-in fetcher: PRAW / official Reddit API
  errors.py              Shared RedditFetchError, used by both fetchers
  ticker_extractor.py  Cashtag/ticker regex extraction + known-ticker validation
  sentiment.py          VADER + WSB slang/emoji lexicon
  aggregator.py         Combines mentions + sentiment into ranked scores, caches results
  models.py             Pydantic response models
  desktop.py             Desktop entry point (pywebview window + opt-in praw setup prompt)
  data/                 S&P 500 + WSB-favorites (trusted) and full-market (cashtag-only) ticker lists
frontend/
  index.html / style.css / app.js   Static dashboard (no build step)
assets/
  icon.ico             App icon, generated by scripts/generate_icon.py
build_exe.py           PyInstaller build script for the desktop .exe
```

## Tuning

Create a `.env` (`cp .env.example .env`) to override any of these — none are required for the default `arctic_shift` source:

- `SUBREDDIT` — analyze a different subreddit.
- `ARCTIC_SHIFT_WINDOW_HOURS` — `arctic_shift` only: how many hours back to pull posts from.
- `ARCTIC_SHIFT_MAX_COMMENT_FETCHES` — `arctic_shift` only: how many of the highest-scoring posts to fetch comments for. Comment-fetching costs one HTTP request per post (no batch endpoint), so this bounds refresh time regardless of `POST_LIMIT` — with defaults, a full refresh takes single-digit seconds.
- `POST_LISTING` — `praw` only: `hot`, `new`, `top`, or `rising`. Comma-separate several (e.g. `hot,rising`, the default) to merge them, deduplicated — `hot` alone skews toward posts that have been popular for a while, so mixing in `rising` keeps the ranking from leaning entirely on stale threads.
- `POST_LIMIT` — how many posts to pull per refresh (per listing, for `praw`).
- `COMMENTS_PER_POST` — how many top-level comments to analyze per post (0 = titles/selftext only, faster).
- `CACHE_TTL_SECONDS` — how long results are cached before re-fetching.

## Disclaimer

Built for educational and portfolio purposes. Nothing in this project is
investment advice. Reddit sentiment is not a reliable predictor of stock
price movement — always do your own research before making financial
decisions.
