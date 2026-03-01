"""
Actian VectorAI DB integration module.
Handles collection management, vector storage, and retrieval via the CortexClient.
"""

import logging
import time
from typing import List, Dict, Optional, Tuple, Any

import numpy as np
from cortex import CortexClient, DistanceMetric

logger = logging.getLogger(__name__)

COLLECTION_NAME = "news_embeddings"


class ActianVectorDB:
    """Manages connections and operations with Actian VectorAI DB."""

    def __init__(self, address: str = "localhost:50051", embedding_dim: int = 384):
        """
        Initialize connection to VectorAI DB.

        Args:
            address: gRPC address of the VectorAI DB server (host:port)
            embedding_dim: Dimension of embedding vectors
        """
        self.address = address
        self.embedding_dim = embedding_dim
        self._client: Optional[CortexClient] = None
        logger.info(f"Initialized ActianVectorDB targeting {address}")

    def connect(self) -> CortexClient:
        """
        Get or create a reusable client connection.

        Returns:
            Connected CortexClient instance

        Raises:
            ConnectionError: If the server is unreachable
        """
        if self._client is None:
            try:
                self._client = CortexClient(self.address)
                self._client.__enter__()
                version, uptime = self._client.health_check()
                logger.info(f"Connected to VectorAI DB: {version}")
            except Exception as e:
                self._client = None
                logger.error(f"Failed to connect to VectorAI DB at {self.address}: {e}")
                raise ConnectionError(
                    f"Cannot connect to VectorAI DB at {self.address}. "
                    f"Is the container running? Error: {e}"
                ) from e
        return self._client

    def initialize_schema(self) -> None:
        """
        Create the news_embeddings collection if it doesn't exist.

        Raises:
            ConnectionError: If the server is unreachable
        """
        client = self.connect()
        try:
            if client.has_collection(COLLECTION_NAME):
                logger.info(f"Collection '{COLLECTION_NAME}' already exists")
                return

            client.create_collection(
                name=COLLECTION_NAME,
                dimension=self.embedding_dim,
                distance_metric=DistanceMetric.COSINE,
            )
            logger.info(
                f"Created collection '{COLLECTION_NAME}' "
                f"(dim={self.embedding_dim}, metric=COSINE)"
            )
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    def insert_embeddings(
        self,
        ticker: str,
        articles: List[Dict[str, str]],
        embeddings: np.ndarray,
    ) -> int:
        """
        Insert article embeddings into the collection.

        Args:
            ticker: Stock ticker symbol
            articles: List of article dictionaries
            embeddings: Numpy array of embeddings (shape: [n_articles, embedding_dim])

        Returns:
            Number of vectors inserted

        Raises:
            ValueError: If articles and embeddings lengths don't match
        """
        if len(articles) != len(embeddings):
            raise ValueError(
                f"Articles count ({len(articles)}) must match "
                f"embeddings count ({len(embeddings)})"
            )
        if len(articles) == 0:
            logger.warning("No articles to insert")
            return 0

        client = self.connect()

        # Build parallel lists for batch_upsert
        base_id = int(time.time() * 1000)  # ms-epoch as unique base ID
        ids: List[int] = []
        vectors: List[List[float]] = []
        payloads: List[Dict[str, Any]] = []

        for idx, (article, embedding) in enumerate(zip(articles, embeddings)):
            ids.append(base_id + idx)
            vectors.append(embedding.tolist())
            payloads.append({
                "ticker": ticker,
                "headline": article["headline"],
                "content": article["summary"],
                "link": article.get("link", ""),
                "timestamp": article.get("timestamp", ""),
            })

        try:
            client.batch_upsert(
                COLLECTION_NAME,
                ids=ids,
                vectors=vectors,
                payloads=payloads,
            )
            logger.info(f"Inserted {len(ids)} embeddings for {ticker}")
            return len(ids)
        except Exception as e:
            logger.error(f"Failed to insert embeddings: {e}")
            raise

    def search_similar(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
    ) -> List[Any]:
        """
        Search for the most similar vectors in the collection.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of search results with id, score, and payload
        """
        client = self.connect()
        try:
            results = client.search(
                COLLECTION_NAME,
                query=query_vector.tolist(),
                top_k=top_k,
                with_payload=True,
            )
            logger.info(f"Search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_collection_count(self) -> int:
        """
        Get the number of vectors in the collection.

        Returns:
            Vector count
        """
        client = self.connect()
        try:
            return client.count(COLLECTION_NAME)
        except Exception as e:
            logger.error(f"Failed to get collection count: {e}")
            return 0

    def close(self) -> None:
        """Close the client connection."""
        if self._client is not None:
            try:
                self._client.__exit__(None, None, None)
                logger.info("VectorAI DB connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self._client = None
