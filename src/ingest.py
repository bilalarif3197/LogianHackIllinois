"""
ingest.py — High-throughput batch sentiment pipeline for user-supplied data.

Randomly samples 100 articles from the full ~1020-article mock feed and
runs them through a single batched FinBERT inference call.

Usage:
    python src/ingest.py                # random sample from mock feed
    python src/ingest.py data.json      # load from JSON file

JSON format:
    {
        "NVDA": [
            {"source": "Bloomberg", "headline": "...", "summary": "..."},
            ...
        ],
        ...
    }
"""

import json
import sys
import random
import time
from typing import Dict, List

import numpy as np
from transformers import pipeline

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from mock_feed import MOCK_FEED

ARTICLES_PER_TICKER = 3   # guarantees every ticker appears in output

# ── Helpers ───────────────────────────────────────────────────────────────────

def _label_to_score(label: str, confidence: float) -> float:
    label = label.lower()
    if "positive" in label:
        return confidence
    elif "negative" in label:
        return -confidence
    return 0.0


def _recommendation(score: float) -> str:
    if score >= 0.3:
        return "BUY"
    elif score <= -0.3:
        return "SELL"
    return "HOLD"


def _sample(feed: Dict[str, List[Dict]], n: int) -> Dict[str, List[Dict]]:
    """Stratified sample: draw n random articles per ticker so every ticker appears."""
    return {
        ticker: random.sample(articles, min(n, len(articles)))
        for ticker, articles in feed.items()
    }


# ── Core pipeline ─────────────────────────────────────────────────────────────

def run(feed: Dict[str, List[Dict[str, str]]]) -> None:
    sampled = _sample(feed, ARTICLES_PER_TICKER)
    total_articles = sum(len(v) for v in sampled.values())

    print(f"Sampled {total_articles} articles across {len(sampled)} tickers")
    print("Loading FinBERT... ", end="", flush=True)
    t0 = time.perf_counter()

    sentiment_pipe = pipeline(
        "sentiment-analysis",
        model="ProsusAI/finbert",
        tokenizer="ProsusAI/finbert",
        truncation=True,
        max_length=512,
        batch_size=64,
    )
    print(f"done ({time.perf_counter() - t0:.1f}s)")

    # Flatten all sampled articles into one ordered list
    tickers: List[str] = list(sampled.keys())
    all_texts: List[str] = []
    boundaries: List[int] = []

    for ticker in tickers:
        boundaries.append(len(all_texts))
        for art in sampled[ticker]:
            all_texts.append(f"{art['headline']} {art['summary']}"[:512])

    print(f"Running inference on {len(all_texts)} articles... ", end="", flush=True)
    t1 = time.perf_counter()

    raw = sentiment_pipe(all_texts)

    print(f"done ({time.perf_counter() - t1:.2f}s)\n")

    # Reconstruct per-ticker aggregate scores
    results = []
    for i, ticker in enumerate(tickers):
        start = boundaries[i]
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(all_texts)
        chunk = raw[start:end]

        scores = [_label_to_score(r["label"], r["score"]) for r in chunk]
        confs  = [r["score"] for r in chunk]
        total_conf = sum(confs) or 1.0
        agg = float(np.clip(
            sum(s * c for s, c in zip(scores, confs)) / total_conf,
            -1.0, 1.0,
        ))
        results.append((ticker, agg, len(chunk)))

    total_time = time.perf_counter() - t0

    print(f"{'─' * 56}")
    for ticker, score, n in results:
        rec = _recommendation(score)
        print(f"TICKER: {ticker:<6}  RECOMMENDATION: {rec:<5}  SCORE: {score:+.3f}  ({n} articles)")
    print(f"{'─' * 56}")
    print(f"Total: {len(results)} tickers | {len(all_texts)} articles | {total_time:.2f}s")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path) as f:
            feed = json.load(f)
        total = sum(len(v) for v in feed.values())
        print(f"Loaded {total} articles across {len(feed)} tickers from {path}")
    else:
        total = sum(len(v) for v in MOCK_FEED.values())
        print(f"Mock feed: {total} articles across {len(MOCK_FEED)} tickers")
        feed = MOCK_FEED

    run(feed)


if __name__ == "__main__":
    main()
