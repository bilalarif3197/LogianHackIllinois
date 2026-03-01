"""
Background sentiment engine — runs the full pipeline (scrape → embed → store → score)
for each monitored ticker and broadcasts results via WebSocket.
"""

import asyncio
import logging
import random
from datetime import datetime

import numpy as np

from api.state import AppState, TickerState
from api.ws import manager

logger = logging.getLogger(__name__)

CYCLE_INTERVAL_SECONDS = 10
MAX_HISTORY = 100


def _recommendation(score: float) -> str:
    if score >= 0.3:
        return "BUY"
    elif score <= -0.3:
        return "SELL"
    return "HOLD"


async def _broadcast_progress(ticker: str, step: str):
    """Push a pipeline progress update to all WebSocket clients."""
    await manager.broadcast({
        "type": "pipeline_progress",
        "data": {"ticker": ticker, "step": step},
    })


async def _refill_queue(ts: TickerState, app_state: AppState):
    """Refill a ticker's article queue from the appropriate data source."""
    loop = asyncio.get_event_loop()

    if app_state.data_source == "mock":
        from mock_feed import MOCK_FEED
        articles = MOCK_FEED.get(ts.ticker, [])
        if not articles:
            return
        shuffled = list(articles)
        random.shuffle(shuffled)
        # Adapt mock articles to match scraper output format
        ts.article_queue = [
            {
                "headline": a["headline"],
                "summary": a["summary"],
                "source": a.get("source", ""),
                "link": "",
                "ticker": ts.ticker,
                "timestamp": datetime.now().isoformat(),
            }
            for a in shuffled
        ]
    else:
        # Live mode: scrape Yahoo Finance in a thread
        try:
            articles = await loop.run_in_executor(
                None, app_state.scraper.scrape_news, ts.ticker, 10
            )
            ts.article_queue = articles
        except Exception as e:
            logger.warning(f"Live scrape failed for {ts.ticker}: {e}")
            ts.article_queue = []


async def _run_pipeline_for_ticker(ts: TickerState, app_state: AppState):
    """Run the full pipeline for a single ticker's queued articles."""
    loop = asyncio.get_event_loop()

    if not ts.article_queue:
        await _refill_queue(ts, app_state)
        if not ts.article_queue:
            return

    articles = ts.article_queue
    ts.article_queue = []

    # Step 1: Scraping (already done — articles are in hand)
    ts.pipeline_step = "scraping"
    await _broadcast_progress(ts.ticker, "scraping")

    # Step 2: Generate embeddings
    ts.pipeline_step = "embedding"
    await _broadcast_progress(ts.ticker, "embedding")
    try:
        embeddings = await loop.run_in_executor(
            None, app_state.embedding_generator.generate_embeddings, articles
        )
    except Exception as e:
        logger.error(f"Embedding failed for {ts.ticker}: {e}")
        return

    # Step 3: Store in VectorAI DB
    ts.pipeline_step = "storing"
    await _broadcast_progress(ts.ticker, "storing")
    if app_state.db:
        try:
            await loop.run_in_executor(
                None, app_state.db.insert_embeddings, ts.ticker, articles, embeddings
            )
        except Exception as e:
            logger.warning(f"DB insert failed for {ts.ticker} (non-fatal): {e}")

    # Step 4: Score with FinBERT
    ts.pipeline_step = "scoring"
    await _broadcast_progress(ts.ticker, "scoring")
    try:
        sentiments = await loop.run_in_executor(
            None, app_state.scorer.analyze_sentiment, articles
        )
    except Exception as e:
        logger.error(f"Scoring failed for {ts.ticker}: {e}")
        return

    # Step 5: Update running aggregate score
    for s in sentiments:
        ts.weighted_sum += s["sentiment_score"] * s["confidence"]
        ts.total_confidence += s["confidence"]
    ts.articles_consumed += len(sentiments)

    if ts.total_confidence > 0:
        ts.current_score = float(np.clip(
            ts.weighted_sum / ts.total_confidence, -1.0, 1.0
        ))
    ts.recommendation = _recommendation(ts.current_score)

    # Keep top 3 most influential articles
    sorted_sentiments = sorted(
        sentiments,
        key=lambda x: abs(x["sentiment_score"]) * x["confidence"],
        reverse=True,
    )
    ts.latest_articles = [
        {
            "headline": s["headline"],
            "label": s["label"],
            "confidence": s["confidence"],
            "sentiment_score": s["sentiment_score"],
            "source": next(
                (a.get("source", "") for a in articles if a["headline"] == s["headline"]),
                "",
            ),
        }
        for s in sorted_sentiments[:3]
    ]

    # Append to score history
    now = datetime.now().isoformat()
    ts.score_history.append((now, ts.current_score))
    if len(ts.score_history) > MAX_HISTORY:
        ts.score_history = ts.score_history[-MAX_HISTORY:]

    ts.pipeline_step = "done"

    # Broadcast score update
    await manager.broadcast({
        "type": "score_update",
        "data": {
            "ticker": ts.ticker,
            "score": ts.current_score,
            "recommendation": ts.recommendation,
            "timestamp": now,
            "articles_processed": ts.articles_consumed,
            "articles_total": ts.articles_consumed + len(ts.article_queue),
            "top_articles": ts.latest_articles,
        },
    })


async def _engine_loop(app_state: AppState):
    """Main engine loop — processes each monitored ticker sequentially per cycle."""
    logger.info("Background engine started")

    while app_state.monitoring_active:
        active = [ts for ts in app_state.tickers.values() if ts.is_monitoring]

        if not active:
            await asyncio.sleep(1)
            continue

        for ts in active:
            if not app_state.monitoring_active:
                break
            try:
                await _run_pipeline_for_ticker(ts, app_state)
            except Exception as e:
                logger.error(f"Pipeline error for {ts.ticker}: {e}")

        await asyncio.sleep(CYCLE_INTERVAL_SECONDS)

    logger.info("Background engine stopped")


def start_engine(app):
    """Start the background engine task if not already running."""
    app_state = app.state.app
    if app_state.engine_task and not app_state.engine_task.done():
        return  # Already running

    app_state.engine_task = asyncio.create_task(_engine_loop(app_state))
