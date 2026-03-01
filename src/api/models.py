"""
Pydantic request/response schemas for the dashboard API.
"""

from typing import Literal
from pydantic import BaseModel


# --- Requests ---

class MonitorRequest(BaseModel):
    tickers: list[str]
    action: Literal["start", "stop"]


class DataSourceRequest(BaseModel):
    source: Literal["mock", "live"]


# --- Responses ---

class TickerInfo(BaseModel):
    ticker: str
    company_name: str
    sector: str
    descriptor: str


class ArticleSentiment(BaseModel):
    headline: str
    label: str
    confidence: float
    sentiment_score: float
    source: str


class TickerScore(BaseModel):
    ticker: str
    score: float
    recommendation: str
    timestamp: str
    articles_processed: int
    articles_total: int
    pipeline_step: str
    top_articles: list[ArticleSentiment]


class ScorePoint(BaseModel):
    timestamp: str
    score: float


class ScoreHistory(BaseModel):
    ticker: str
    history: list[ScorePoint]


class EngineStatus(BaseModel):
    monitoring_active: bool
    data_source: str
    monitored_tickers: list[str]
    models_loaded: bool
