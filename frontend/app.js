const API_BASE = window.location.origin;

const state = {
  tab: "bullish",
  data: null,
};

const els = {
  status: document.getElementById("status"),
  table: document.getElementById("table"),
  tbody: document.getElementById("table-body"),
  meta: document.getElementById("meta"),
  refresh: document.getElementById("refresh"),
  tabs: document.querySelectorAll(".nav-item"),
  statGrid: document.getElementById("stat-grid"),
  trendingList: document.getElementById("trending-list"),
  flairMix: document.getElementById("flair-mix"),
  tableTitle: document.getElementById("table-title"),
};

const TAB_LABELS = {
  bullish: "Bullish Tickers",
  bearish: "Bearish Tickers",
  all: "All Mentions",
};

// Mirrors the backend's own flair-reliability weighting (see aggregator.py
// FLAIR_WEIGHTS) so the "Post Mix" chart's colors carry the same meaning as
// the ranking algorithm: blue = higher-signal analysis, orange = noise.
const FLAIR_COLORS = {
  dd: "#2f6fed",
  discussion: "#4d84ef",
  fundamentals: "#3f7ef2",
  news: "#6a97f1",
  "technical analysis": "#6a97f1",
  meme: "#c65d2e",
  shitpost: "#d4784f",
  yolo: "#8a8a86",
  gain: "#8a8a86",
  loss: "#8a8a86",
  chart: "#8a8a86",
};
const FLAIR_COLOR_FALLBACK = "#c7c6c1";

function flairColor(label) {
  return FLAIR_COLORS[label.toLowerCase()] || FLAIR_COLOR_FALLBACK;
}

function sentimentBucketLabel(v) {
  if (v > 0.25) return "Bullish";
  if (v > 0.08) return "Mildly bullish";
  if (v < -0.25) return "Bearish";
  if (v < -0.08) return "Mildly bearish";
  return "Mixed / neutral";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function fmtSentiment(v) {
  const sign = v > 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}`;
}

function fmtTimeAgo(unixSeconds) {
  const diff = Math.max(0, Date.now() / 1000 - unixSeconds);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

const CHART_ROW_HEIGHT = 28;
const CHART_BAR_THICKNESS = 18;
const CHART_WIDTH = 640;
const CHART_MAX_MOVERS = 6;

function renderChart() {
  const container = document.getElementById("chart-container");
  if (!state.data) {
    container.innerHTML = "";
    return;
  }

  const bullish = state.data.bullish.slice(0, CHART_MAX_MOVERS);
  const bearish = state.data.bearish.slice(0, CHART_MAX_MOVERS);
  const movers = [...bullish, ...bearish].sort((a, b) => b.score - a.score);

  if (movers.length === 0) {
    container.innerHTML = "";
    return;
  }

  const maxAbsScore = Math.max(...movers.map((m) => Math.abs(m.score)), 0.01);
  const centerX = CHART_WIDTH / 2;
  const maxBarHalf = CHART_WIDTH / 2 - 70;
  const scale = maxBarHalf / maxAbsScore;
  const height = movers.length * CHART_ROW_HEIGHT;

  const bars = movers
    .map((m, i) => {
      const y = i * CHART_ROW_HEIGHT + (CHART_ROW_HEIGHT - CHART_BAR_THICKNESS) / 2;
      const barW = Math.max(Math.abs(m.score) * scale, 2);
      const isBull = m.score >= 0;
      const barX = isBull ? centerX : centerX - barW;
      const color = isBull ? "var(--bull)" : "var(--bear)";
      const ticker = escapeHtml(m.ticker);
      const tickerLabelX = isBull ? centerX - 8 : centerX + 8;
      const tickerAnchor = isBull ? "end" : "start";
      const valueLabelX = isBull ? barX + barW + 8 : barX - 8;
      const valueAnchor = isBull ? "start" : "end";
      const titleText = escapeHtml(`${m.ticker}: score ${m.score.toFixed(2)}, ${m.mentions} mentions`);

      return `
        <rect class="chart-bar" x="${barX.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${CHART_BAR_THICKNESS}" rx="4" fill="${color}">
          <title>${titleText}</title>
        </rect>
        <text class="chart-bar-label" x="${tickerLabelX.toFixed(1)}" y="${(y + CHART_BAR_THICKNESS / 2 + 4).toFixed(1)}" text-anchor="${tickerAnchor}">${ticker}</text>
        <text class="chart-bar-value" x="${valueLabelX.toFixed(1)}" y="${(y + CHART_BAR_THICKNESS / 2 + 4).toFixed(1)}" text-anchor="${valueAnchor}">${m.score.toFixed(2)}</text>`;
    })
    .join("");

  container.innerHTML = `
    <svg viewBox="0 0 ${CHART_WIDTH} ${height}" width="100%" height="${height}" role="img" aria-label="Top mover tickers by bullish/bearish score">
      <line class="chart-baseline" x1="${centerX}" y1="0" x2="${centerX}" y2="${height}" />
      ${bars}
    </svg>`;
}

function renderStats() {
  const d = state.data;
  const topBull = d.bullish[0];
  const topBear = d.bearish[0];
  const overall = d.overall_sentiment;

  const cards = [
    { label: "Posts Analyzed", value: d.posts_analyzed },
    { label: "Tickers Tracked", value: d.all.length },
    {
      label: "Overall Sentiment",
      value: fmtSentiment(overall),
      sub: sentimentBucketLabel(overall),
      cls: overall > 0.08 ? "bull" : overall < -0.08 ? "bear" : "",
    },
    {
      label: "High-Signal Posts",
      value: `${d.high_quality_post_pct.toFixed(0)}%`,
      sub: "flaired DD / Discussion / News",
    },
    {
      label: "Top Bullish",
      value: topBull ? escapeHtml(topBull.ticker) : "—",
      sub: topBull ? `score ${topBull.score.toFixed(2)}` : "no signal yet",
      cls: "bull",
    },
    {
      label: "Top Bearish",
      value: topBear ? escapeHtml(topBear.ticker) : "—",
      sub: topBear ? `score ${topBear.score.toFixed(2)}` : "no signal yet",
      cls: "bear",
    },
  ];

  els.statGrid.innerHTML = cards
    .map(
      (c) => `
        <div class="stat-card">
          <div class="stat-label">${c.label}</div>
          <div class="stat-value ${c.cls || ""}">${c.value}</div>
          ${c.sub ? `<div class="stat-sub">${c.sub}</div>` : ""}
        </div>`
    )
    .join("");
}

function renderFlairMix() {
  const breakdown = state.data.flair_breakdown;

  if (!breakdown || breakdown.length === 0) {
    els.flairMix.innerHTML = `<div class="empty-note">No post-flair data yet.</div>`;
    return;
  }

  const total = breakdown.reduce((sum, f) => sum + f.count, 0);

  const bar = breakdown
    .map((f) => {
      const pct = total ? (100 * f.count) / total : 0;
      return `<span class="flair-mix-segment" style="width:${pct.toFixed(2)}%;background:${flairColor(f.flair)}" title="${escapeHtml(f.flair)}: ${f.count}"></span>`;
    })
    .join("");

  const rows = breakdown
    .map(
      (f) => `
        <div class="flair-row">
          <span class="flair-row-label"><span class="flair-dot" style="background:${flairColor(f.flair)}"></span>${escapeHtml(f.flair)}</span>
          <span class="flair-row-count">${f.count}</span>
        </div>`
    )
    .join("");

  els.flairMix.innerHTML = `<div class="flair-mix-bar">${bar}</div><div class="flair-list">${rows}</div>`;
}

function renderTrending() {
  const top = [...state.data.all].sort((a, b) => b.mentions - a.mentions).slice(0, 6);

  if (top.length === 0) {
    els.trendingList.innerHTML = `<div class="empty-note">Nothing trending yet.</div>`;
    return;
  }

  els.trendingList.innerHTML = top
    .map(
      (t, i) => `
        <div class="trending-row">
          <span><span class="trending-rank">${i + 1}</span><span class="trending-ticker">${escapeHtml(t.ticker)}</span></span>
          <span class="sentiment-badge sentiment-${t.sentiment_label}">${t.mentions} mentions</span>
        </div>`
    )
    .join("");
}

function render() {
  if (!state.data) return;
  renderChart();
  renderStats();
  renderTrending();
  renderFlairMix();
  els.tableTitle.textContent = TAB_LABELS[state.tab] || "Tickers";
  const rows = state.data[state.tab] || [];

  if (rows.length === 0) {
    els.status.textContent = "No tickers found in this category yet. Try refreshing.";
    els.status.classList.remove("hidden");
    els.table.classList.add("hidden");
    return;
  }

  els.status.classList.add("hidden");
  els.table.classList.remove("hidden");

  els.tbody.innerHTML = rows
    .map((row, i) => {
      const samples = row.sample_posts
        .map((p) => {
          const href = escapeHtml(p.permalink);
          const title = escapeHtml(p.title);
          return `<a href="${href}" target="_blank" rel="noopener" title="${title}">${title}</a>`;
        })
        .join("");
      return `
        <tr>
          <td class="rank">${i + 1}</td>
          <td class="ticker">${escapeHtml(row.ticker)}</td>
          <td class="company">${escapeHtml(row.company_name)}</td>
          <td>${row.mentions}</td>
          <td><span class="sentiment-badge sentiment-${row.sentiment_label}">${fmtSentiment(row.avg_sentiment)}</span></td>
          <td class="score-value">${row.score.toFixed(2)}</td>
          <td class="sample-posts">${samples}</td>
        </tr>`;
    })
    .join("");
}

const FETCH_MAX_ATTEMPTS = 3;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchSuggestionsWithRetry(forceRefresh) {
  let lastErr;
  for (let attempt = 1; attempt <= FETCH_MAX_ATTEMPTS; attempt++) {
    try {
      const res = await fetch(`${API_BASE}/api/suggestions${forceRefresh ? "?refresh=true" : ""}`);
      if (!res.ok) {
        // A bare "Not Found" (no JSON body) here is very likely the hosting
        // platform dropping this one request, not a real app-level error —
        // worth a retry rather than surfacing it immediately.
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed: ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      lastErr = err;
      if (attempt < FETCH_MAX_ATTEMPTS) await sleep(600 * attempt);
    }
  }
  throw lastErr;
}

async function load(forceRefresh = false) {
  els.refresh.disabled = true;
  els.status.classList.remove("hidden", "error");
  els.status.textContent = forceRefresh
    ? "Refreshing from Reddit… (this can take a bit if comments are being analyzed)"
    : "Loading…";
  els.table.classList.add("hidden");

  try {
    state.data = await fetchSuggestionsWithRetry(forceRefresh);
    els.meta.textContent = `r/${state.data.subreddit} · ${state.data.posts_analyzed} posts analyzed · updated ${fmtTimeAgo(state.data.generated_at)}`;
    render();
  } catch (err) {
    els.status.textContent = `Failed to load suggestions:\n${err.message}`;
    els.status.classList.add("error");
    els.table.classList.add("hidden");
  } finally {
    els.refresh.disabled = false;
  }
}

els.tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    els.tabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    state.tab = tab.dataset.tab;
    render();
  });
});

els.refresh.addEventListener("click", () => load(true));

load(false);
