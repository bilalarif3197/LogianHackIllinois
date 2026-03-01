# Logian — Stock Sentiment Analysis System

A HackIllinois project that analyzes stock sentiment from live financial news using NLP models and vector search, producing BUY/SELL/HOLD recommendations via three interfaces: CLI, real-time streaming dashboard, and local vector DB lookup tool.

## How It Works

Given a stock ticker, the pipeline:

1. **Scrapes** news headlines and summaries from Yahoo Finance RSS feeds
2. **Generates embeddings** using `all-MiniLM-L6-v2` (sentence-transformers, 384-dim)
3. **Stores embeddings** in Actian VectorAI DB for vector similarity search
4. **Analyzes sentiment** using [FinBERT](https://huggingface.co/ProsusAI/finbert), a BERT model fine-tuned on financial text
5. **Outputs** a weighted sentiment score (-1.0 to +1.0) and BUY/SELL/HOLD recommendation

### Score Interpretation

| Score Range   | Recommendation |
|---------------|----------------|
| 0.3 to 1.0    | **BUY**        |
| -0.3 to 0.3   | **HOLD**       |
| -1.0 to -0.3  | **SELL**       |

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the dashboard frontend)
- Docker (for Actian VectorAI DB)

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
pip install actiancortex-0.1.0b1-py3-none-any.whl
```

### 2. Install dashboard frontend dependencies

```bash
cd dashboard && npm install && cd ..
```

### 3. Start the Actian VectorAI DB

```bash
docker pull williamimoh/actian-vectorai-db:1.0b
docker run -d --name actian-vectorai -p 50051:50051 williamimoh/actian-vectorai-db:1.0b
```

### 4. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env if your DB is running at a different address
```

## Three Ways to Use Logian

### 1. CLI — Single Ticker Analysis

Run the full pipeline for one ticker and get a terminal report:

```bash
python src/main.py NVDA
```

Example output:

```
======================================================================
STOCK SENTIMENT ANALYSIS REPORT
======================================================================

Ticker: NVDA
Recommendation: HOLD
Sentiment Score: -0.1823 (range: -1.0 to 1.0)

Top 3 Most Influential Articles:
----------------------------------------------------------------------
1. Is Nvidia a Buy on the Post-Earnings Dip?
   Sentiment: POSITIVE (84.4% confidence)  Score: 0.8438

2. Nvidia Faces Headwinds Amid Macro Uncertainty
   Sentiment: NEGATIVE (95.4% confidence)  Score: -0.9544
```

### 2. Real-Time Streaming Dashboard

A React + Vite frontend connected to a FastAPI + WebSocket backend. Monitor multiple tickers simultaneously with live pipeline progress and score updates.

```bash
# Start both backend and frontend:
./run.sh

# Or manually:
# Terminal 1 — Backend
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend
cd dashboard && npm run dev
```

Open **http://localhost:5173** in your browser.

Features:
- Select tickers and monitor them in real-time
- Per-ticker pipeline progress (scraping → embedding → storing → scoring → done)
- Color-coded BUY/SELL/HOLD score cards
- Bar chart of all ticker scores and line chart of score history over time
- Toggle between mock data feed and live Yahoo Finance scraping
- All heavy processing runs in background workers — the UI stays responsive

### 3. Local Vector DB Lookup Tool

A self-contained local web UI that queries the Actian VectorAI DB directly — no API server needed. Supports ticker-based lookup and semantic (natural language) search.

```bash
./run.sh lookup

# Or directly:
python src/lookup.py
```

Open **http://localhost:8050** in your browser.

Features:
- **Ticker Lookup**: Enter a ticker symbol, find all stored articles for it
- **Semantic Search**: Enter a natural language query (e.g. "AI chip demand"), find the most similar articles across all tickers
- Deduplicated results (no repeated articles)
- Overall aggregate sentiment score (-1.0 to +1.0) with BUY/SELL/HOLD label
- Per-article FinBERT sentiment scoring in real-time
- Runs entirely locally — connects directly to VectorAI DB via gRPC

### Batch Ingestion

Ingest articles for multiple tickers into the vector DB at once:

```bash
python src/ingest.py
```

Uses the mock feed (1000+ synthetic articles across 100 tickers) to populate the DB for testing.

## Project Structure

```
src/
├── main.py           # CLI pipeline orchestrator
├── scraper.py        # Yahoo Finance news scraper (RSS + HTML fallback)
├── embeddings.py     # Sentence embedding generation (all-MiniLM-L6-v2)
├── database.py       # Actian VectorAI DB integration (gRPC via CortexClient)
├── scoring.py        # FinBERT sentiment analysis and report generation
├── ingest.py         # Batch ingestion script
├── mock_feed.py      # Synthetic article feed for 100 tickers
├── lookup.py         # Local vector DB lookup tool with embedded web UI
└── api/
    ├── server.py     # FastAPI app with lifespan (loads models once at startup)
    ├── routes.py     # REST endpoints (/api/tickers, /api/scores, /api/monitor, etc.)
    ├── ws.py         # WebSocket endpoint + ConnectionManager for real-time push
    ├── engine.py     # Background pipeline engine (scrape → embed → store → score)
    ├── models.py     # Pydantic request/response schemas
    └── state.py      # Shared in-memory application state

dashboard/            # React + Vite + TypeScript frontend
├── src/
│   ├── App.tsx       # Top-level state management + WebSocket dispatch
│   ├── components/   # ScoreCard, ScoreBarChart, SentimentTimeline, TickerSelector, etc.
│   ├── hooks/        # useWebSocket (auto-reconnect), useTickers
│   └── types/        # TypeScript interfaces matching backend models
├── vite.config.ts    # Dev proxy to backend
└── package.json
```

## Restarting the DB

If you restart your machine, bring the container back up with:

```bash
docker start actian-vectorai
```

## Tech Stack

- **Sentiment Model**: FinBERT (ProsusAI/finbert) — financial domain BERT
- **Embedding Model**: all-MiniLM-L6-v2 — 384-dimensional sentence embeddings
- **Vector Database**: Actian VectorAI DB — gRPC-based vector similarity search
- **Backend**: FastAPI + WebSockets + asyncio background workers
- **Frontend**: React + Vite + TypeScript + Recharts
- **Data Source**: Yahoo Finance RSS (live) + synthetic mock feed (testing)

## Disclaimer

This tool is for educational purposes only and does not constitute financial advice.
