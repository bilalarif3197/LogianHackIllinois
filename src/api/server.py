"""
FastAPI application for the stock sentiment dashboard, yay!.
"""

import sys
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.state import AppState
from api.routes import router
from api.ws import ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models once at startup, tear down on shutdown."""
    app_state = AppState()

    logger.info("Loading SentimentScorer (FinBERT)...")
    from scoring import SentimentScorer
    app_state.scorer = SentimentScorer()

    logger.info("Loading EmbeddingGenerator (all-MiniLM-L6-v2)...")
    from embeddings import EmbeddingGenerator
    app_state.embedding_generator = EmbeddingGenerator()

    logger.info("Initializing YahooFinanceScraper...")
    from scraper import YahooFinanceScraper
    app_state.scraper = YahooFinanceScraper()

    # Try to connect to vector DB (non-fatal if unavailable)
    db_address = os.getenv("VECTORAI_DB_ADDRESS", "localhost:50051")
    try:
        from database import ActianVectorDB
        embedding_dim = app_state.embedding_generator.get_embedding_dimension()
        app_state.db = ActianVectorDB(address=db_address, embedding_dim=embedding_dim)
        app_state.db.initialize_schema()
        logger.info("Connected to VectorAI DB")
    except Exception as e:
        logger.warning(f"VectorAI DB unavailable (non-fatal): {e}")
        app_state.db = None

    app_state.models_loaded = True
    app.state.app = app_state

    logger.info("All models loaded. Server ready.")
    yield

    # Shutdown
    if app_state.engine_task and not app_state.engine_task.done():
        app_state.monitoring_active = False
        app_state.engine_task.cancel()
    if app_state.scraper:
        app_state.scraper.close()
    if app_state.db:
        app_state.db.close()
    logger.info("Server shutdown complete.")


app = FastAPI(
    title="Stock Sentiment Dashboard API",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(ws_router)
