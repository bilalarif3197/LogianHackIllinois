"""
Shared in-memory application state for the dashboard backend.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scoring import SentimentScorer
    from embeddings import EmbeddingGenerator
    from scraper import YahooFinanceScraper
    from database import ActianVectorDB


@dataclass
class TickerState:
    """Per-ticker monitoring state."""
    ticker: str
    company_name: str
    sector: str
    current_score: float = 0.0
    recommendation: str = "HOLD"
    score_history: list = field(default_factory=list)      # [(iso_timestamp, score), ...]
    latest_articles: list = field(default_factory=list)     # top 3 scored articles
    article_queue: list = field(default_factory=list)       # articles waiting to be processed
    articles_consumed: int = 0
    is_monitoring: bool = True
    pipeline_step: str = "pending"                          # pending|scraping|embedding|storing|scoring|done
    weighted_sum: float = 0.0                               # running accumulator for aggregate score
    total_confidence: float = 0.0                           # running confidence denominator


@dataclass
class AppState:
    """Global application state shared across routes, WebSocket, and engine."""
    scorer: Optional[object] = None
    embedding_generator: Optional[object] = None
    scraper: Optional[object] = None
    db: Optional[object] = None
    tickers: dict = field(default_factory=dict)             # ticker -> TickerState
    data_source: str = "mock"                               # "mock" or "live"
    monitoring_active: bool = False
    engine_task: Optional[asyncio.Task] = None
    models_loaded: bool = False
