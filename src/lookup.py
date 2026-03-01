"""
lookup.py — Local vector DB lookup tool with a self-contained web UI.

Connects directly to the Actian VectorAI DB and the embedding model.
Supports ticker-based lookup and semantic (natural language) search.
No external API server — just a lightweight local HTTP server.

Usage:
    python src/lookup.py
    # Opens http://localhost:8050 in your browser
"""

import json
import logging
import os
import sys
import webbrowser
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ensure src/ is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("LOOKUP_PORT", "8050"))

# ── HTML UI (self-contained) ────────────────────────────────────────────────

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Logian — Vector DB Lookup</title>
<style>
  :root {
    --bg: #0f1117; --surface: #1a1d27; --border: #2a2d3a;
    --text: #e4e4e7; --muted: #71717a; --accent: #6366f1;
    --green: #22c55e; --red: #ef4444; --yellow: #eab308;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    background: var(--bg); color: var(--text);
    min-height: 100vh; padding: 2rem;
  }
  h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
  .subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 2rem; }
  .tabs {
    display: flex; gap: 0; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border);
  }
  .tab {
    padding: 0.75rem 1.5rem; cursor: pointer; color: var(--muted);
    border-bottom: 2px solid transparent; transition: all 0.2s;
    background: none; border-top: none; border-left: none; border-right: none;
    font-family: inherit; font-size: 0.9rem;
  }
  .tab:hover { color: var(--text); }
  .tab.active { color: var(--accent); border-bottom-color: var(--accent); }
  .panel { display: none; }
  .panel.active { display: block; }
  .search-box {
    display: flex; gap: 0.75rem; margin-bottom: 1.5rem;
  }
  input[type="text"] {
    flex: 1; padding: 0.75rem 1rem; background: var(--surface);
    border: 1px solid var(--border); border-radius: 6px;
    color: var(--text); font-family: inherit; font-size: 0.9rem;
    outline: none; transition: border-color 0.2s;
  }
  input:focus { border-color: var(--accent); }
  button {
    padding: 0.75rem 1.5rem; background: var(--accent); color: white;
    border: none; border-radius: 6px; cursor: pointer;
    font-family: inherit; font-size: 0.9rem; font-weight: 600;
    transition: opacity 0.2s;
  }
  button:hover { opacity: 0.85; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .status {
    padding: 1rem; background: var(--surface); border-radius: 6px;
    margin-bottom: 1.5rem; font-size: 0.85rem; color: var(--muted);
  }
  .status .count { color: var(--accent); font-weight: 600; }
  .results { display: flex; flex-direction: column; gap: 0.75rem; }
  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 1.25rem; transition: border-color 0.2s;
  }
  .card:hover { border-color: var(--accent); }
  .card-header {
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 0.75rem; gap: 1rem;
  }
  .card-headline { font-size: 0.95rem; font-weight: 600; line-height: 1.4; }
  .badge {
    padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.75rem;
    font-weight: 700; white-space: nowrap; flex-shrink: 0;
  }
  .badge-buy { background: rgba(34,197,94,0.15); color: var(--green); }
  .badge-sell { background: rgba(239,68,68,0.15); color: var(--red); }
  .badge-hold { background: rgba(234,179,8,0.15); color: var(--yellow); }
  .card-meta {
    display: flex; gap: 1.5rem; font-size: 0.8rem; color: var(--muted);
    flex-wrap: wrap;
  }
  .card-meta span { display: flex; align-items: center; gap: 0.3rem; }
  .similarity { color: var(--accent); font-weight: 600; }
  .card-content {
    margin-top: 0.75rem; font-size: 0.85rem; color: var(--muted);
    line-height: 1.5;
  }
  .loading {
    text-align: center; padding: 3rem; color: var(--muted);
  }
  .spinner {
    display: inline-block; width: 20px; height: 20px;
    border: 2px solid var(--border); border-top-color: var(--accent);
    border-radius: 50%; animation: spin 0.8s linear infinite;
    margin-right: 0.5rem; vertical-align: middle;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .empty { text-align: center; padding: 3rem; color: var(--muted); }
  .error { color: var(--red); padding: 1rem; background: rgba(239,68,68,0.1); border-radius: 6px; }
  .overall-score {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.25rem 1.5rem; border-radius: 8px; margin-bottom: 1.25rem;
    border: 1px solid var(--border);
  }
  .overall-score.buy { background: rgba(34,197,94,0.08); border-color: rgba(34,197,94,0.3); }
  .overall-score.sell { background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.3); }
  .overall-score.hold { background: rgba(234,179,8,0.08); border-color: rgba(234,179,8,0.3); }
  .overall-label { font-size: 1.1rem; font-weight: 700; }
  .overall-score.buy .overall-label { color: var(--green); }
  .overall-score.sell .overall-label { color: var(--red); }
  .overall-score.hold .overall-label { color: var(--yellow); }
  .overall-number { font-size: 1.8rem; font-weight: 700; font-variant-numeric: tabular-nums; }
  .overall-score.buy .overall-number { color: var(--green); }
  .overall-score.sell .overall-number { color: var(--red); }
  .overall-score.hold .overall-number { color: var(--yellow); }
  .overall-detail { font-size: 0.8rem; color: var(--muted); }
</style>
</head>
<body>
<h1>Logian Vector DB Lookup</h1>
<p class="subtitle">Direct queries against Actian VectorAI DB — ticker lookup &amp; semantic search</p>

<div class="status" id="status">Connecting...</div>

<div class="tabs">
  <button class="tab active" data-panel="ticker-panel">Ticker Lookup</button>
  <button class="tab" data-panel="semantic-panel">Semantic Search</button>
</div>

<div id="ticker-panel" class="panel active">
  <div class="search-box">
    <input type="text" id="ticker-input" placeholder="Enter ticker symbol (e.g. NVDA, AAPL)" />
    <button id="ticker-btn" onclick="tickerSearch()">Search</button>
  </div>
  <div id="ticker-results"></div>
</div>

<div id="semantic-panel" class="panel">
  <div class="search-box">
    <input type="text" id="query-input" placeholder="Natural language query (e.g. AI chip demand, EV market growth)" />
    <button id="query-btn" onclick="semanticSearch()">Search</button>
  </div>
  <div id="semantic-results"></div>
</div>

<script>
// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.panel).classList.add('active');
  });
});

// Enter key support
document.getElementById('ticker-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') tickerSearch();
});
document.getElementById('query-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') semanticSearch();
});

// Fetch DB status on load
fetch('/status').then(r => r.json()).then(data => {
  const el = document.getElementById('status');
  if (data.connected) {
    el.innerHTML = `Connected to VectorAI DB &mdash; <span class="count">${data.count}</span> vectors stored`;
  } else {
    el.innerHTML = `<span class="error">${data.error}</span>`;
  }
}).catch(() => {
  document.getElementById('status').innerHTML = '<span class="error">Cannot reach local server</span>';
});

function renderCard(item) {
  const score = item.sentiment_score || 0;
  let rec = 'HOLD', cls = 'badge-hold';
  if (score >= 0.3) { rec = 'BUY'; cls = 'badge-buy'; }
  else if (score <= -0.3) { rec = 'SELL'; cls = 'badge-sell'; }

  const simHtml = item.similarity != null
    ? `<span>Similarity: <span class="similarity">${(item.similarity * 100).toFixed(1)}%</span></span>` : '';

  return `
    <div class="card">
      <div class="card-header">
        <div class="card-headline">${item.headline || 'Untitled'}</div>
        ${item.sentiment_score != null ? `<div class="badge ${cls}">${rec} ${score >= 0 ? '+' : ''}${score.toFixed(3)}</div>` : ''}
      </div>
      <div class="card-meta">
        <span>Ticker: <strong>${item.ticker || '?'}</strong></span>
        ${simHtml}
        ${item.timestamp ? `<span>${item.timestamp}</span>` : ''}
      </div>
      ${item.content ? `<div class="card-content">${item.content}</div>` : ''}
    </div>`;
}

function showLoading(el) {
  el.innerHTML = '<div class="loading"><span class="spinner"></span> Searching...</div>';
}

function renderOverallScore(overall, heading) {
  if (!overall) return '';
  const s = overall.score;
  const cls = overall.label === 'BUY' ? 'buy' : overall.label === 'SELL' ? 'sell' : 'hold';
  const sign = s >= 0 ? '+' : '';
  return `
    <div class="overall-score ${cls}">
      <div>
        <div class="overall-label">${overall.label}</div>
        <div class="overall-detail">${heading} &mdash; ${overall.article_count} unique article${overall.article_count !== 1 ? 's' : ''}</div>
      </div>
      <div class="overall-number">${sign}${s.toFixed(4)}</div>
    </div>`;
}

async function tickerSearch() {
  const ticker = document.getElementById('ticker-input').value.trim().toUpperCase();
  if (!ticker) return;
  const el = document.getElementById('ticker-results');
  showLoading(el);
  try {
    const res = await fetch(`/search/ticker?ticker=${encodeURIComponent(ticker)}`);
    const data = await res.json();
    if (data.error) { el.innerHTML = `<div class="error">${data.error}</div>`; return; }
    if (!data.results.length) { el.innerHTML = '<div class="empty">No articles found for this ticker in the vector DB.</div>'; return; }
    el.innerHTML = renderOverallScore(data.overall_score, `Overall Sentiment for ${ticker}`)
      + '<div class="results">' + data.results.map(renderCard).join('') + '</div>';
  } catch (e) {
    el.innerHTML = `<div class="error">Search failed: ${e.message}</div>`;
  }
}

async function semanticSearch() {
  const query = document.getElementById('query-input').value.trim();
  if (!query) return;
  const el = document.getElementById('semantic-results');
  showLoading(el);
  try {
    const res = await fetch(`/search/semantic?q=${encodeURIComponent(query)}&top_k=10`);
    const data = await res.json();
    if (data.error) { el.innerHTML = `<div class="error">${data.error}</div>`; return; }
    if (!data.results.length) { el.innerHTML = '<div class="empty">No similar articles found.</div>'; return; }
    el.innerHTML = renderOverallScore(data.overall_score, `Overall Sentiment`)
      + '<div class="results">' + data.results.map(renderCard).join('') + '</div>';
  } catch (e) {
    el.innerHTML = `<div class="error">Search failed: ${e.message}</div>`;
  }
}
</script>
</body>
</html>"""


# ── Server ───────────────────────────────────────────────────────────────────

class LookupComponents:
    """Holds loaded models and DB connection."""
    def __init__(self):
        self.db = None
        self.embedding_generator = None
        self.scorer = None
        self.db_connected = False
        self.db_error = ""


def load_components() -> LookupComponents:
    """Load models and connect to DB at startup."""
    comp = LookupComponents()

    logger.info("Loading EmbeddingGenerator (all-MiniLM-L6-v2)...")
    from embeddings import EmbeddingGenerator
    comp.embedding_generator = EmbeddingGenerator()

    logger.info("Loading SentimentScorer (FinBERT)...")
    from scoring import SentimentScorer
    comp.scorer = SentimentScorer()

    db_address = os.getenv("VECTORAI_DB_ADDRESS", "localhost:50051")
    try:
        from database import ActianVectorDB
        embedding_dim = comp.embedding_generator.get_embedding_dimension()
        comp.db = ActianVectorDB(address=db_address, embedding_dim=embedding_dim)
        comp.db.connect()
        comp.db_connected = True
        logger.info("Connected to VectorAI DB")
    except Exception as e:
        comp.db_error = str(e)
        logger.warning(f"VectorAI DB unavailable: {e}")

    return comp


class LookupHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the lookup UI."""

    def __init__(self, components: LookupComponents, *args, **kwargs):
        self.components = components
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/" or path == "":
            self._send_html(HTML_PAGE)

        elif path == "/status":
            if self.components.db_connected:
                try:
                    count = self.components.db.get_collection_count()
                except Exception:
                    count = 0
                self._send_json({"connected": True, "count": count})
            else:
                self._send_json({"connected": False, "error": self.components.db_error})

        elif path == "/search/ticker":
            ticker = params.get("ticker", [""])[0].upper()
            if not ticker:
                self._send_json({"error": "Missing ticker parameter"}, 400)
                return
            self._handle_ticker_search(ticker)

        elif path == "/search/semantic":
            query = params.get("q", [""])[0]
            top_k = int(params.get("top_k", ["10"])[0])
            if not query:
                self._send_json({"error": "Missing q parameter"}, 400)
                return
            self._handle_semantic_search(query, top_k)

        else:
            self.send_error(404)

    def _handle_ticker_search(self, ticker: str):
        """Search by ticker: embed the ticker name and search, then filter by payload."""
        if not self.components.db_connected:
            self._send_json({"error": "VectorAI DB not connected"})
            return

        try:
            # Generate an embedding for the ticker to find related articles
            query_text = f"{ticker} stock news"
            query_vec = self.components.embedding_generator.generate_single_embedding(query_text)

            # Search with a high top_k and filter by ticker in payload
            raw_results = self.components.db.search_similar(query_vec, top_k=50)

            # Deduplicate by headline, keeping the highest-similarity result
            seen = {}
            for r in raw_results:
                payload = r.payload if hasattr(r, "payload") else {}
                if payload.get("ticker", "").upper() != ticker:
                    continue
                headline = payload.get("headline", "")
                score = r.score if hasattr(r, "score") else 0
                if headline not in seen or score > seen[headline][1]:
                    seen[headline] = (r, score)

            results = []
            for headline, (r, _) in seen.items():
                payload = r.payload if hasattr(r, "payload") else {}
                content = payload.get("content", "")
                sentiment = self._score_article(headline, content)
                results.append({
                    "headline": headline,
                    "content": content,
                    "ticker": payload.get("ticker", ""),
                    "timestamp": payload.get("timestamp", ""),
                    "similarity": r.score if hasattr(r, "score") else None,
                    **sentiment,
                })

            # Sort by similarity descending
            results.sort(key=lambda x: x.get("similarity") or 0, reverse=True)

            # Compute overall aggregate score (-1 to +1)
            overall_score = self._compute_overall_score(results)

            self._send_json({"results": results, "overall_score": overall_score})

        except Exception as e:
            logger.error(f"Ticker search failed: {e}")
            self._send_json({"error": str(e)})

    def _handle_semantic_search(self, query: str, top_k: int):
        """Semantic search: embed the query and find most similar articles."""
        if not self.components.db_connected:
            self._send_json({"error": "VectorAI DB not connected"})
            return

        try:
            query_vec = self.components.embedding_generator.generate_single_embedding(query)
            # Fetch extra results so we still get top_k unique after dedup
            raw_results = self.components.db.search_similar(query_vec, top_k=top_k * 3)

            # Deduplicate by headline, keeping highest similarity
            seen = {}
            for r in raw_results:
                payload = r.payload if hasattr(r, "payload") else {}
                headline = payload.get("headline", "")
                score = r.score if hasattr(r, "score") else 0
                if headline not in seen or score > seen[headline][1]:
                    seen[headline] = (r, score)

            results = []
            for headline, (r, _) in seen.items():
                payload = r.payload if hasattr(r, "payload") else {}
                content = payload.get("content", "")
                sentiment = self._score_article(headline, content)
                results.append({
                    "headline": headline,
                    "content": content,
                    "ticker": payload.get("ticker", ""),
                    "timestamp": payload.get("timestamp", ""),
                    "similarity": r.score if hasattr(r, "score") else None,
                    **sentiment,
                })

            # Sort by similarity descending, limit to requested top_k
            results.sort(key=lambda x: x.get("similarity") or 0, reverse=True)
            results = results[:top_k]

            # Compute overall aggregate score (-1 to +1)
            overall_score = self._compute_overall_score(results)

            self._send_json({"results": results, "overall_score": overall_score})

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            self._send_json({"error": str(e)})

    def _compute_overall_score(self, results: list) -> dict:
        """Compute a weighted-average overall score from individual article scores."""
        if not results:
            return {"score": 0.0, "label": "HOLD", "article_count": 0}

        # Weight by similarity so more relevant articles matter more
        total_weight = 0.0
        weighted_sum = 0.0
        for r in results:
            sim = r.get("similarity") or 0.5
            sent = r.get("sentiment_score", 0.0)
            weighted_sum += sim * sent
            total_weight += sim

        score = weighted_sum / total_weight if total_weight > 0 else 0.0
        score = max(-1.0, min(1.0, score))  # clamp

        if score >= 0.3:
            label = "BUY"
        elif score <= -0.3:
            label = "SELL"
        else:
            label = "HOLD"

        return {"score": round(score, 4), "label": label, "article_count": len(results)}

    def _score_article(self, headline: str, content: str) -> dict:
        """Run FinBERT on a single article and return sentiment info."""
        try:
            text = f"{headline} {content}"[:512]
            result = self.components.scorer.sentiment_pipeline(text)[0]
            label = result["label"].lower()
            confidence = result["score"]
            if "positive" in label:
                score = confidence
            elif "negative" in label:
                score = -confidence
            else:
                score = 0.0
            return {
                "label": label,
                "confidence": confidence,
                "sentiment_score": score,
            }
        except Exception:
            return {"label": "neutral", "confidence": 0.0, "sentiment_score": 0.0}


def main():
    logger.info("Starting Logian Vector DB Lookup...")
    components = load_components()

    handler = partial(LookupHandler, components)
    server = HTTPServer(("localhost", PORT), handler)

    url = f"http://localhost:{PORT}"
    logger.info(f"Lookup UI running at {url}")
    print(f"\n  Logian Vector DB Lookup")
    print(f"  {url}\n")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()
        if components.db:
            components.db.close()


if __name__ == "__main__":
    main()
