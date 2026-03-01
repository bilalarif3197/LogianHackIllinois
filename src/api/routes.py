"""
REST API endpoints for the dashboard.
"""

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from api.models import (
    MonitorRequest,
    DataSourceRequest,
    TickerInfo,
    TickerScore,
    ArticleSentiment,
    ScorePoint,
    ScoreHistory,
    EngineStatus,
)
from api.state import TickerState

router = APIRouter()

# Ticker catalog — imported lazily to avoid circular imports at module level
_ticker_catalog: Optional[list] = None


def _get_ticker_catalog():
    global _ticker_catalog
    if _ticker_catalog is None:
        from mock_feed import TICKERS
        _ticker_catalog = TICKERS
    return _ticker_catalog


def _get_ticker_lookup() -> dict:
    return {t[0]: t for t in _get_ticker_catalog()}


def _get_app_state(request: Request):
    return request.app.state.app


def _build_engine_status(app_state) -> EngineStatus:
    return EngineStatus(
        monitoring_active=app_state.monitoring_active,
        data_source=app_state.data_source,
        monitored_tickers=[
            t for t, s in app_state.tickers.items() if s.is_monitoring
        ],
        models_loaded=app_state.models_loaded,
    )


def _build_ticker_score(ts: TickerState) -> TickerScore:
    return TickerScore(
        ticker=ts.ticker,
        score=ts.current_score,
        recommendation=ts.recommendation,
        timestamp=datetime.now().isoformat(),
        articles_processed=ts.articles_consumed,
        articles_total=ts.articles_consumed + len(ts.article_queue),
        pipeline_step=ts.pipeline_step,
        top_articles=[
            ArticleSentiment(
                headline=a.get("headline", ""),
                label=a.get("label", "neutral"),
                confidence=a.get("confidence", 0.0),
                sentiment_score=a.get("sentiment_score", 0.0),
                source=a.get("source", ""),
            )
            for a in ts.latest_articles
        ],
    )


@router.get("/tickers", response_model=list[TickerInfo])
async def get_tickers():
    """Return the full catalog of available tickers."""
    return [
        TickerInfo(
            ticker=ticker,
            company_name=name,
            sector=sector,
            descriptor=desc,
        )
        for ticker, name, sector, desc in _get_ticker_catalog()
    ]


@router.get("/scores", response_model=list[TickerScore])
async def get_scores(request: Request):
    """Return current scores for all monitored tickers."""
    app_state = _get_app_state(request)
    return [
        _build_ticker_score(ts)
        for ts in app_state.tickers.values()
        if ts.is_monitoring
    ]


@router.get("/scores/{ticker}", response_model=TickerScore)
async def get_score(ticker: str, request: Request):
    """Return current score for a single monitored ticker."""
    app_state = _get_app_state(request)
    ticker = ticker.upper()
    ts = app_state.tickers.get(ticker)
    if not ts or not ts.is_monitoring:
        raise HTTPException(status_code=404, detail=f"{ticker} is not being monitored")
    return _build_ticker_score(ts)


@router.get("/history/{ticker}", response_model=ScoreHistory)
async def get_history(ticker: str, request: Request):
    """Return score history for a monitored ticker."""
    app_state = _get_app_state(request)
    ticker = ticker.upper()
    ts = app_state.tickers.get(ticker)
    if not ts:
        raise HTTPException(status_code=404, detail=f"{ticker} is not being monitored")
    return ScoreHistory(
        ticker=ticker,
        history=[
            ScorePoint(timestamp=t, score=s) for t, s in ts.score_history
        ],
    )


@router.post("/monitor", response_model=EngineStatus)
async def monitor(body: MonitorRequest, request: Request):
    """Start or stop monitoring for a set of tickers."""
    app_state = _get_app_state(request)
    lookup = _get_ticker_lookup()

    if body.action == "start":
        for ticker in body.tickers:
            ticker = ticker.upper()
            if ticker not in lookup:
                raise HTTPException(status_code=400, detail=f"Unknown ticker: {ticker}")
            if ticker not in app_state.tickers:
                _, name, sector, _ = lookup[ticker]
                app_state.tickers[ticker] = TickerState(
                    ticker=ticker,
                    company_name=name,
                    sector=sector,
                )
            else:
                app_state.tickers[ticker].is_monitoring = True

        # Start the engine if not already running
        if not app_state.monitoring_active:
            app_state.monitoring_active = True
            from api.engine import start_engine
            start_engine(request.app)

    elif body.action == "stop":
        for ticker in body.tickers:
            ticker = ticker.upper()
            ts = app_state.tickers.get(ticker)
            if ts:
                ts.is_monitoring = False

        # Stop engine if no tickers are being monitored
        active = [t for t, s in app_state.tickers.items() if s.is_monitoring]
        if not active:
            app_state.monitoring_active = False

    return _build_engine_status(app_state)


@router.post("/source", response_model=EngineStatus)
async def set_source(body: DataSourceRequest, request: Request):
    """Toggle between mock and live data source."""
    app_state = _get_app_state(request)
    app_state.data_source = body.source

    # Clear article queues so they refill from the new source
    for ts in app_state.tickers.values():
        ts.article_queue.clear()

    return _build_engine_status(app_state)


@router.get("/status", response_model=EngineStatus)
async def get_status(request: Request):
    """Return current engine status."""
    return _build_engine_status(_get_app_state(request))
