"""
Main pipeline orchestrator for stock sentiment scoring system.
"""

import logging
import sys
import os
from dotenv import load_dotenv

# Ensure src/ is on the import path regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import YahooFinanceScraper
from embeddings import EmbeddingGenerator
from database import ActianVectorDB
from scoring import SentimentScorer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sentiment_analysis.log')
    ]
)

logger = logging.getLogger(__name__)


class StockSentimentPipeline:
    """End-to-end pipeline for stock sentiment analysis."""

    def __init__(self, db_address: str = "localhost:50051"):
        """
        Initialize the pipeline components.

        Args:
            db_address: VectorAI DB gRPC address (host:port)
        """
        logger.info("Initializing Stock Sentiment Pipeline")

        # Initialize components
        self.scraper = YahooFinanceScraper()
        self.embedding_generator = EmbeddingGenerator()
        self.scorer = SentimentScorer()

        # Initialize database with embedding dimension
        embedding_dim = self.embedding_generator.get_embedding_dimension()
        self.db = ActianVectorDB(
            address=db_address,
            embedding_dim=embedding_dim,
        )

        # Ensure collection exists
        try:
            self.db.initialize_schema()
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise

        logger.info("Pipeline initialized successfully")

    def run(self, ticker: str, max_articles: int = 10) -> dict:
        """
        Run the complete sentiment analysis pipeline.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
            max_articles: Maximum number of articles to analyze

        Returns:
            Dictionary containing score, recommendation, and tip sheet

        Raises:
            Exception: On pipeline failures
        """
        logger.info(f"Starting sentiment analysis for {ticker}")

        try:
            # Step 1: Scrape news articles
            logger.info("Step 1: Scraping news articles")
            articles = self.scraper.scrape_news(ticker, max_articles=max_articles)
            logger.info(f"Scraped {len(articles)} articles")

            # Step 2: Generate embeddings
            logger.info("Step 2: Generating embeddings")
            embeddings = self.embedding_generator.generate_embeddings(articles)
            logger.info(f"Generated embeddings with shape {embeddings.shape}")

            # Step 3: Store in VectorAI DB
            logger.info("Step 3: Storing embeddings in VectorAI DB")
            inserted_count = self.db.insert_embeddings(ticker, articles, embeddings)
            logger.info(f"Inserted {inserted_count} records into database")

            # Step 4: Analyze sentiment
            logger.info("Step 4: Analyzing sentiment")
            sentiments = self.scorer.analyze_sentiment(articles)

            # Step 5: Calculate aggregate score
            logger.info("Step 5: Calculating aggregate score")
            aggregate_score, top_articles = self.scorer.calculate_aggregate_score(sentiments)

            # Step 6: Generate tip sheet
            logger.info("Step 6: Generating tip sheet")
            tip_sheet = self.scorer.generate_tip_sheet(ticker, aggregate_score, top_articles)

            logger.info(f"Pipeline completed successfully for {ticker}")

            return {
                'ticker': ticker,
                'score': aggregate_score,
                'recommendation': self._get_recommendation(aggregate_score),
                'tip_sheet': tip_sheet,
                'article_count': len(articles),
                'sentiments': sentiments
            }

        except Exception as e:
            logger.error(f"Pipeline failed for {ticker}: {e}")
            raise

    def _get_recommendation(self, score: float) -> str:
        """
        Get trading recommendation based on score.

        Args:
            score: Sentiment score

        Returns:
            Recommendation string
        """
        if score >= 0.3:
            return "BUY"
        elif score <= -0.3:
            return "SELL"
        else:
            return "HOLD"

    def cleanup(self):
        """Clean up resources."""
        self.scraper.close()
        self.db.close()
        logger.info("Pipeline cleanup completed")


def main():
    """Main entry point for the application."""
    # Load environment variables
    load_dotenv()

    # Get database address from environment
    db_address = os.getenv('VECTORAI_DB_ADDRESS', 'localhost:50051')

    # Get ticker from command line or prompt
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        ticker = input("Enter stock ticker symbol (e.g., NVDA, AAPL): ").upper()

    if not ticker:
        logger.error("Ticker symbol is required")
        sys.exit(1)

    # Initialize and run pipeline
    pipeline = None
    try:
        pipeline = StockSentimentPipeline(db_address=db_address)

        # Run analysis
        result = pipeline.run(ticker)

        # Print results
        print("\n" + "="*70)
        print("SENTIMENT ANALYSIS COMPLETE")
        print("="*70)
        print(f"\nTicker: {result['ticker']}")
        print(f"Sentiment Score: {result['score']:.4f}")
        print(f"Recommendation: {result['recommendation']}")
        print(f"Articles Analyzed: {result['article_count']}")
        print("\n" + result['tip_sheet'])

    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)
    finally:
        if pipeline:
            pipeline.cleanup()


if __name__ == "__main__":
    main()
