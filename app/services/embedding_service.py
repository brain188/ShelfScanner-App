"""
Embedding service for generating vector representations of books.
"""
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings for books"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize embedding model"""
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load sentence transformer model"""
        try:
            self._model = SentenceTransformer(settings.embedding_model)
            logger.info("Embedding model loaded", model=settings.embedding_model)
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            raise
    
    def generate_book_embedding(self, title: str, authors: List[str], description: str = "") -> List[float]:
        """Generate embedding for a book"""
        try:
            # Combine book information
            text = f"{title}. By {', '.join(authors)}. {description[:500]}"
            
            # Generate embedding
            embedding = self._model.encode(text, convert_to_numpy=True)
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            return []
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query"""
        try:
            embedding = self._model.encode(query, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error("Failed to generate query embedding", error=str(e))
            return []


embedding_service = EmbeddingService()