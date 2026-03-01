"""
signals.py — Dual-path sentiment signal engine.

Fast Path  — Pure NumPy cosine similarity against cached risk-anchor vectors.
             Article embeddings are pre-seeded into Actian VectorAI DB (and
             mirrored in-memory). Signal computation is entirely in NumPy.
             Latency: microseconds.

Slow Path  — Full FinBERT inference for high-accuracy sentiment scoring.
             Confirmed embeddings are written back to Actian and appended
             to the in-memory anchor cache, improving fast-path accuracy
             over time (feedback loop).
             Latency: seconds.

Usage:
    python src/signals.py              # fast path all tickers, slow path 10
    python src/signals.py --fast       # fast path only
    python src/signals.py --slow N     # slow path on N random tickers
"""

import sys
import os
import time
import random
import logging
import argparse
from typing import Dict, List, Optional, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mock_feed import MOCK_FEED

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ── Risk anchor phrases ───────────────────────────────────────────────────────
# These are embedded once at startup and cached in memory as the reference
# signal space. The slow path appends confirmed embeddings here over time.

ANCHORS: Dict[str, List[str]] = {
    "positive": [
        "record revenue growth beats analyst estimates raises guidance",
        "strong earnings beat operating margin expansion exceeds expectations",
        "market share gains accelerating new customer wins enterprise",
        "new product launch drives strong demand backlog pipeline",
        "share buyback program signals management confidence undervalued",
        "analyst upgrade price target raised buy recommendation outperform",
        "dividend increase shareholder returns free cash flow record",
        "strategic partnership hyperscaler contract win revenue accretive synergies",
    ],
    "negative": [
        "SEC investigation regulatory probe antitrust lawsuit fine penalty",
        "earnings miss cuts guidance demand weakness inventory buildup channel",
        "CEO departure executive resignation strategic uncertainty succession",
        "data breach cybersecurity incident customer records regulatory risk fine",
        "product recall safety defect liability exposure NHTSA FDA",
        "short interest surge bearish thesis valuation concern overvalued",
        "supply chain disruption margin pressure elevated input costs headwind",
        "class action lawsuit accounting irregularities restatement write-down",
    ],
}

# ── Signal Engine ─────────────────────────────────────────────────────────────

class SignalEngine:
    """
    Manages the fast and slow signal paths and the feedback loop between them.

    Fast path reads pre-seeded embeddings from the in-memory store (backed by
    Actian VectorAI DB when available) and computes cosine similarity against
    the anchor cache entirely in NumPy.

    Slow path runs FinBERT inference, writes confirmed embeddings back to
    Actian, and appends the averaged embedding to the anchor cache so future
    fast-path queries benefit from the confirmed signal.
    """

    def __init__(self, db_address: str = "localhost:50051"):
        print("Loading embedding model (all-MiniLM-L6-v2)...", flush=True)
        from embeddings import EmbeddingGenerator
        self.embedder = EmbeddingGenerator()

        # FinBERT is lazy-loaded only when the slow path is invoked
        self._scorer = None

        # Actian VectorAI DB connection (non-fatal if unavailable)
        self._db = None
        self._init_db(db_address)

        # In-memory embedding store: ticker → np.ndarray (n_articles, dim)
        # Populated by seed_articles(); updated by slow_path().
        self._store: Dict[str, np.ndarray] = {}

        # Anchor cache: label → list of L2-normalized embedding vectors
        # Starts with the hardcoded phrases above; grows as slow path confirms scores.
        self._anchors: Dict[str, List[np.ndarray]] = {"positive": [], "negative": []}
        self._anchor_count_initial = 0
        self._seed_anchors()

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_db(self, address: str) -> None:
        try:
            from database import ActianVectorDB
            dim = 384  # all-MiniLM-L6-v2 output dimension
            self._db = ActianVectorDB(address=address, embedding_dim=dim)
            self._db.initialize_schema()
            print(f"Connected to Actian VectorAI DB at {address}")
        except Exception as e:
            print(f"Actian DB unavailable — using in-memory store ({e})")
            self._db = None

    def _seed_anchors(self) -> None:
        """Embed all hardcoded anchor phrases and populate the anchor cache."""
        for label, phrases in ANCHORS.items():
            for phrase in phrases:
                vec = self.embedder.generate_single_embedding(phrase)
                self._anchors[label].append(vec)
        n = sum(len(v) for v in self._anchors.values())
        self._anchor_count_initial = n
        print(f"Seeded {n} risk anchors ({len(ANCHORS['positive'])} positive, "
              f"{len(ANCHORS['negative'])} negative)")

    def seed_articles(self, feed: Dict[str, List[Dict]]) -> None:
        """
        Pre-embed all articles in the feed and store embeddings in Actian
        (if available) and the in-memory store.

        This is the one-time seeding step that enables microsecond fast-path
        lookups — no inference happens during fast_path() after this.
        """
        total_articles = sum(len(v) for v in feed.values())
        print(f"Seeding {total_articles} articles across {len(feed)} tickers...",
              flush=True)
        t0 = time.perf_counter()

        for ticker, articles in feed.items():
            embeddings = self.embedder.generate_embeddings(articles)
            self._store[ticker] = embeddings  # in-memory mirror

            if self._db:
                try:
                    self._db.insert_embeddings(ticker, articles, embeddings)
                except Exception as e:
                    logger.warning(f"Actian insert failed for {ticker}: {e}")

        elapsed = time.perf_counter() - t0
        print(f"Seeded {total_articles} embeddings in {elapsed:.1f}s\n")

    # ── Fast Path ─────────────────────────────────────────────────────────────

    def fast_path(self, ticker: str) -> Tuple[float, int]:
        """
        Fast path: retrieve stored embeddings from the in-memory store
        (backed by Actian) and compute cosine similarity against the anchor
        cache entirely in NumPy. No ML inference.

        Returns:
            (signal, elapsed_nanoseconds)
        """
        t0 = time.perf_counter_ns()

        embeddings = self._store.get(ticker)
        if embeddings is None or len(embeddings) == 0:
            return 0.0, time.perf_counter_ns() - t0

        # Aggregate the ticker's articles into a single representative vector.
        # All embeddings are L2-normalised, so the mean is a valid centroid.
        avg_vec = np.mean(embeddings, axis=0)
        avg_vec /= (np.linalg.norm(avg_vec) + 1e-9)  # re-normalise

        # Stack anchor matrices for vectorised dot products
        pos_mat = np.array(self._anchors["positive"])   # (n_pos, dim)
        neg_mat = np.array(self._anchors["negative"])   # (n_neg, dim)

        # Cosine similarity = dot product (vectors are L2-normalised)
        pos_sims = pos_mat @ avg_vec   # (n_pos,)
        neg_sims = neg_mat @ avg_vec   # (n_neg,)

        # Net signal: positive pull minus negative pull, scaled to [-1, 1]
        raw = float(np.mean(pos_sims) - np.mean(neg_sims))
        signal = float(np.clip(raw * 3.0, -1.0, 1.0))

        elapsed_ns = time.perf_counter_ns() - t0
        return signal, elapsed_ns

    # ── Slow Path ─────────────────────────────────────────────────────────────

    def slow_path(self, ticker: str, articles: List[Dict]) -> Tuple[float, float]:
        """
        Slow path: full FinBERT inference for high-accuracy sentiment scoring.

        After scoring, the confirmed embedding is:
          1. Written back to Actian (persistent update).
          2. Appended to the in-memory anchor cache (feedback loop) so
             future fast-path queries for similar tickers benefit.

        Returns:
            (score, elapsed_seconds)
        """
        t0 = time.perf_counter()

        # Lazy-load FinBERT only when slow path is first called
        if self._scorer is None:
            print("  [slow] Loading FinBERT (one-time)...", flush=True)
            from scoring import SentimentScorer
            self._scorer = SentimentScorer()

        sentiments = self._scorer.analyze_sentiment(articles)
        score, _ = self._scorer.calculate_aggregate_score(sentiments)

        # Re-embed articles with confirmed sentiment context
        embeddings = self.embedder.generate_embeddings(articles)
        self._store[ticker] = embeddings  # update in-memory store

        if self._db:
            try:
                self._db.insert_embeddings(
                    ticker, articles, embeddings
                )
            except Exception as e:
                logger.warning(f"Actian update failed for {ticker}: {e}")

        # Feedback loop: add confirmed embedding to anchor cache
        avg_embedding = np.mean(embeddings, axis=0)
        avg_embedding /= (np.linalg.norm(avg_embedding) + 1e-9)

        if score > 0.1:
            self._anchors["positive"].append(avg_embedding)
        elif score < -0.1:
            self._anchors["negative"].append(avg_embedding)

        elapsed = time.perf_counter() - t0
        return score, elapsed

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def anchor_count(self) -> int:
        return sum(len(v) for v in self._anchors.values())

    def cleanup(self) -> None:
        if self._db:
            self._db.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rec(score: float) -> str:
    if score >= 0.3:
        return "BUY"
    elif score <= -0.3:
        return "SELL"
    return "HOLD"


# ── Runner ────────────────────────────────────────────────────────────────────

def run(feed: Dict[str, List[Dict]], n_slow: int = 10) -> None:
    engine = SignalEngine()
    engine.seed_articles(feed)

    tickers = list(feed.keys())
    slow_set = set(random.sample(tickers, min(n_slow, len(tickers))))

    # Load FinBERT upfront so its load time doesn't pollute per-ticker timings
    if slow_set:
        print(f"Running slow path on {len(slow_set)} tickers: {', '.join(sorted(slow_set))}\n")
        print("  [slow] Loading FinBERT (one-time)...", flush=True)
        from scoring import SentimentScorer
        engine._scorer = SentimentScorer()
        print("  [slow] FinBERT ready.\n")

    col = "{:<6}  {:>11}  {:>10}  {:>11}  {:>10}  {:>4}  {}"
    header = col.format("TICKER", "FAST SIG", "FAST TIME", "SLOW SIG", "SLOW TIME", "REC", "PATH")
    sep = "─" * len(header)
    print(sep)
    print(header)
    print(sep)

    fast_times = []
    slow_times = []
    initial_anchors = engine._anchor_count_initial
    anchors_added = 0

    for ticker in tickers:
        fast_signal, fast_ns = engine.fast_path(ticker)
        fast_us = fast_ns / 1_000
        fast_times.append(fast_us)

        if ticker in slow_set:
            slow_score, slow_s = engine.slow_path(ticker, feed[ticker])
            slow_times.append(slow_s * 1_000)
            new_anchors = engine.anchor_count - initial_anchors - anchors_added
            anchors_added += new_anchors
            slow_sig_str  = f"{slow_score:>+.4f}"
            slow_time_str = f"{slow_s * 1000:.0f}ms"
            path_str      = "FAST + SLOW"
        else:
            slow_sig_str  = "—"
            slow_time_str = "—"
            path_str      = "FAST"

        rec = _rec(fast_signal)
        print(col.format(
            ticker,
            f"{fast_signal:>+.4f}",
            f"{fast_us:.1f}μs",
            slow_sig_str,
            slow_time_str,
            rec,
            path_str,
        ))

    print(sep)

    avg_fast = sum(fast_times) / len(fast_times)
    avg_slow = sum(slow_times) / len(slow_times) if slow_times else 0
    speedup  = (avg_slow * 1_000) / avg_fast if avg_fast and avg_slow else 0

    print(f"\nFast path  — avg {avg_fast:.1f}μs / ticker  ({len(fast_times)} tickers)")
    if slow_times:
        print(f"Slow path  — avg {avg_slow:.0f}ms / ticker  ({len(slow_times)} tickers)  "
              f"[{speedup:,.0f}x slower than fast path]")
    print(f"Anchor cache — {initial_anchors} initial → {engine.anchor_count} "
          f"(+{anchors_added} confirmed from slow path)")

    engine.cleanup()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Dual-path sentiment signal engine")
    parser.add_argument("--fast", action="store_true", help="Fast path only, skip FinBERT")
    parser.add_argument("--slow", type=int, default=10, metavar="N",
                        help="Number of tickers to run slow path on (default: 10)")
    args = parser.parse_args()

    n_slow = 0 if args.fast else args.slow
    run(MOCK_FEED, n_slow=n_slow)


if __name__ == "__main__":
    main()
