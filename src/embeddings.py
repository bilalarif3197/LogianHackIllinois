"""
Embedding generation module.
Converts text into vector representations using sentence-transformers.
"""

import logging
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for text content using sentence-transformers."""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedding generator.

        Args:
            model_name: Name of the sentence-transformer model to use
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")

    def generate_embeddings(self, articles: List[Dict[str, str]]) -> np.ndarray:
        """
        Generate embeddings for a list of articles.

        Args:
            articles: List of article dictionaries with 'headline' and 'summary' keys

        Returns:
            Normalized numpy array of embeddings (shape: [n_articles, embedding_dim])

        Raises:
            ValueError: If articles list is empty
        """
        if not articles:
            raise ValueError("Cannot generate embeddings for empty article list")

        # Combine headline and summary for richer context
        texts = [
            f"{article['headline']} {article['summary']}"
            for article in articles
        ]

        logger.info(f"Generating embeddings for {len(texts)} articles")

        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True  # L2 normalization
        )

        logger.info(f"Generated embeddings with shape: {embeddings.shape}")

        return embeddings

    def generate_single_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Normalized embedding vector
        """
        embedding = self.model.encode(
            text,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return embedding

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.

        Returns:
            Embedding dimension
        """
        return self.embedding_dim
