# Logian — Stock Sentiment Analysis Pipeline

A HackIllinois project that analyzes stock sentiment from live financial news and produces BUY/SELL/HOLD recommendations.

## How It Works

Given a stock ticker, the pipeline:

1. **Scrapes** news headlines and summaries from Yahoo Finance RSS feeds
2. **Generates embeddings** using `all-MiniLM-L6-v2` (sentence-transformers)
3. **Stores embeddings** in Actian VectorAI DB for vector search
4. **Analyzes sentiment** using [FinBERT](https://huggingface.co/ProsusAI/finbert), a BERT model fine-tuned on financial text
5. **Outputs** a weighted sentiment score and tip sheet with a BUY/SELL/HOLD recommendation

### Score Interpretation

| Score Range   | Recommendation |
|---------------|----------------|
| 0.3 to 1.0    | **BUY**        |
| -0.3 to 0.3   | **HOLD**       |
| -1.0 to -0.3  | **SELL**       |

## Setup

### Prerequisites

- Python 3.10+
- Docker

### 1. Install dependencies

```bash
pip install -r requirements.txt
pip install actiancortex-0.1.0b1-py3-none-any.whl
```

### 2. Start the Actian VectorAI DB

```bash
docker pull williamimoh/actian-vectorai-db:1.0b
docker run -d --name actian-vectorai -p 50051:50051 williamimoh/actian-vectorai-db:1.0b
```

### 3. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env if your DB is running at a different address
```

### 4. Run

```bash
python src/main.py NVDA
```

You will be prompted for a ticker if you don't pass one as an argument.

## Usage

```bash
python src/main.py <TICKER>

# Examples
python src/main.py AAPL
python src/main.py TSLA
python src/main.py MSFT
```

### Example Output

```
======================================================================
STOCK SENTIMENT ANALYSIS REPORT
======================================================================

Ticker: NVDA
Recommendation: HOLD
Sentiment Score: -0.1823 (range: -1.0 to 1.0)

======================================================================
REASONING
======================================================================

Recent news indicates negative sentiment for NVDA.

Top 3 Most Influential Articles:
----------------------------------------------------------------------

1. Is Nvidia a Buy on the Post-Earnings Dip?
   Sentiment: POSITIVE (84.4% confidence)
   Score: 0.8438

2. Nvidia Faces Headwinds Amid Macro Uncertainty
   Sentiment: NEGATIVE (95.4% confidence)
   Score: -0.9544
...
```

## Project Structure

```
src/
├── main.py        # Pipeline orchestrator and entry point
├── scraper.py     # Yahoo Finance news scraper (RSS + HTML fallback)
├── embeddings.py  # Sentence embedding generation (all-MiniLM-L6-v2)
├── database.py    # Actian VectorAI DB integration (gRPC via cortex SDK)
└── scoring.py     # FinBERT sentiment analysis and tip sheet generation
```

## Restarting the DB

If you restart your machine, bring the container back up with:

```bash
docker start actian-vectorai
```

## Disclaimer

This tool is for educational purposes only and does not constitute financial advice.
