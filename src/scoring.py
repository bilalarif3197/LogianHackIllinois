"""
Sentiment scoring module.
Analyzes embeddings and news content to generate sentiment scores.
"""

import logging
from typing import List, Dict, Tuple
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)


class SentimentScorer:
    """Generates sentiment scores for financial news using FinBERT."""

    def __init__(self, model_name: str = "ProsusAI/finbert"):
        """
        Initialize the sentiment scorer with a financial sentiment model.

        Args:
            model_name: Name of the pretrained sentiment model
        """
        logger.info(f"Loading sentiment model: {model_name}")

        try:
            # Load FinBERT model for financial sentiment analysis
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer
            )
            logger.info("Sentiment model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load {model_name}, falling back to basic model: {e}")
            # Fallback to a simpler model
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )

    def analyze_sentiment(self, articles: List[Dict[str, str]]) -> List[Dict[str, any]]:
        """
        Analyze sentiment for a list of articles.

        Args:
            articles: List of article dictionaries

        Returns:
            List of sentiment analysis results with scores and labels

        Raises:
            ValueError: If articles list is empty
        """
        if not articles:
            raise ValueError("Cannot analyze sentiment for empty article list")

        logger.info(f"Analyzing sentiment for {len(articles)} articles")

        sentiments = []
        for idx, article in enumerate(articles):
            try:
                # Combine headline and summary for analysis
                text = f"{article['headline']} {article['summary']}"

                # Truncate to model's max length (512 tokens)
                text = text[:512]

                # Get sentiment prediction
                result = self.sentiment_pipeline(text)[0]

                # Convert to numerical score [-1, 1]
                score = self._convert_to_score(result)

                sentiments.append({
                    'article_idx': idx,
                    'headline': article['headline'],
                    'label': result['label'],
                    'confidence': result['score'],
                    'sentiment_score': score,
                    'link': article.get('link', '')
                })

            except Exception as e:
                logger.warning(f"Failed to analyze article {idx}: {e}")
                # Assign neutral sentiment on error
                sentiments.append({
                    'article_idx': idx,
                    'headline': article.get('headline', 'Unknown'),
                    'label': 'neutral',
                    'confidence': 0.0,
                    'sentiment_score': 0.0,
                    'link': article.get('link', '')
                })

        logger.info(f"Completed sentiment analysis for {len(sentiments)} articles")
        return sentiments

    def _convert_to_score(self, result: Dict[str, any]) -> float:
        """
        Convert sentiment label and confidence to numerical score [-1, 1].

        Args:
            result: Sentiment pipeline result with 'label' and 'score'

        Returns:
            Sentiment score between -1 (negative) and 1 (positive)
        """
        label = result['label'].lower()
        confidence = result['score']

        # FinBERT labels: positive, negative, neutral
        if 'positive' in label:
            return confidence
        elif 'negative' in label:
            return -confidence
        else:  # neutral
            return 0.0

    def calculate_aggregate_score(
        self,
        sentiments: List[Dict[str, any]]
    ) -> Tuple[float, List[Dict[str, any]]]:
        """
        Calculate aggregate sentiment score and identify top influential articles.

        Args:
            sentiments: List of sentiment analysis results

        Returns:
            Tuple of (aggregate_score, top_articles)
            - aggregate_score: Mean sentiment score normalized to [-1, 1]
            - top_articles: Top 3 most influential articles
        """
        if not sentiments:
            return 0.0, []

        # Calculate weighted average (weight by confidence)
        weighted_scores = [
            s['sentiment_score'] * s['confidence']
            for s in sentiments
        ]
        total_confidence = sum(s['confidence'] for s in sentiments)

        if total_confidence == 0:
            aggregate_score = 0.0
        else:
            aggregate_score = sum(weighted_scores) / total_confidence

        # Ensure score is in [-1, 1] range
        aggregate_score = np.clip(aggregate_score, -1.0, 1.0)

        # Identify top 3 most influential articles
        # Sort by absolute sentiment score weighted by confidence
        sorted_sentiments = sorted(
            sentiments,
            key=lambda x: abs(x['sentiment_score']) * x['confidence'],
            reverse=True
        )
        top_articles = sorted_sentiments[:3]

        logger.info(f"Aggregate sentiment score: {aggregate_score:.4f}")

        return aggregate_score, top_articles

    def generate_tip_sheet(
        self,
        ticker: str,
        aggregate_score: float,
        top_articles: List[Dict[str, any]]
    ) -> str:
        """
        Generate human-readable tip sheet explaining the sentiment analysis.

        Args:
            ticker: Stock ticker symbol
            aggregate_score: Aggregate sentiment score
            top_articles: Top influential articles

        Returns:
            Formatted tip sheet string
        """
        # Determine recommendation
        if aggregate_score >= 0.3:
            recommendation = "BUY"
        elif aggregate_score <= -0.3:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"

        # Build tip sheet
        tip_sheet = f"""
{'='*70}
STOCK SENTIMENT ANALYSIS REPORT
{'='*70}

Ticker: {ticker}
Recommendation: {recommendation}
Sentiment Score: {aggregate_score:.4f} (range: -1.0 to 1.0)
Score Interpretation:
  • -1.0 to -0.3: Strong Negative (SELL)
  • -0.3 to  0.3: Neutral (HOLD)
  •  0.3 to  1.0: Strong Positive (BUY)

{'='*70}
REASONING
{'='*70}
"""

        if aggregate_score > 0:
            sentiment_desc = "positive sentiment"
        elif aggregate_score < 0:
            sentiment_desc = "negative sentiment"
        else:
            sentiment_desc = "neutral sentiment"

        tip_sheet += f"\nRecent news indicates {sentiment_desc} for {ticker}.\n"
        tip_sheet += "\nTop 3 Most Influential Articles:\n"
        tip_sheet += "-" * 70 + "\n"

        for idx, article in enumerate(top_articles, 1):
            sentiment_label = article['label'].upper()
            confidence_pct = article['confidence'] * 100

            tip_sheet += f"\n{idx}. {article['headline']}\n"
            tip_sheet += f"   Sentiment: {sentiment_label} ({confidence_pct:.1f}% confidence)\n"
            tip_sheet += f"   Score: {article['sentiment_score']:.4f}\n"
            if article.get('link'):
                tip_sheet += f"   Link: {article['link']}\n"

        tip_sheet += "\n" + "="*70 + "\n"
        tip_sheet += "DISCLAIMER: This analysis is based on recent news sentiment and\n"
        tip_sheet += "should not be considered financial advice. Always conduct thorough\n"
        tip_sheet += "research before making investment decisions.\n"
        tip_sheet += "="*70 + "\n"

        return tip_sheet
