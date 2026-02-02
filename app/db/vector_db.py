"""
Vector database client for book embeddings and similarity search.
Implements Qdrant client with connection pooling.
"""
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorDBClient:
    """
    Vector database client wrapper for Qdrant.
    Manages collections and vector operations.
    """
    
    _instance: Optional["VectorDBClient"] = None
    _client: Optional[QdrantClient] = None
    
    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Qdrant client"""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Qdrant client with configuration"""
        try:
            self._client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                api_key=settings.qdrant_api_key,
                timeout=30.0
            )
            
            # Ensure collection exists
            self._ensure_collection()
            
            logger.info("Vector DB client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Vector DB client", error=str(e))
            raise
    
    def _ensure_collection(self):
        """Ensure the books collection exists"""
        try:
            collections = self._client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if settings.qdrant_collection_name not in collection_names:
                self._client.create_collection(
                    collection_name=settings.qdrant_collection_name,
                    vectors_config=VectorParams(
                        size=384,  # Size for all-MiniLM-L6-v2 embeddings
                        distance=Distance.COSINE
                    )
                )
                logger.info(
                    "Created vector collection",
                    collection=settings.qdrant_collection_name
                )
            else:
                logger.debug(
                    "Vector collection already exists",
                    collection=settings.qdrant_collection_name
                )
                
        except Exception as e:
            logger.error("Failed to ensure collection exists", error=str(e))
            raise
    
    @property
    def client(self) -> QdrantClient:
        """Get Qdrant client instance"""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    async def upsert_book_embedding(
        self,
        book_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Insert or update book embedding.
        
        Args:
            book_id: Unique book identifier
            embedding: Vector embedding
            metadata: Book metadata for filtering
        
        Returns:
            True if successful
        """
        try:
            point = PointStruct(
                id=book_id,
                vector=embedding,
                payload=metadata
            )
            
            self._client.upsert(
                collection_name=settings.qdrant_collection_name,
                points=[point]
            )
            
            logger.debug("Book embedding upserted", book_id=book_id)
            return True
            
        except Exception as e:
            logger.error(
                "Failed to upsert book embedding",
                book_id=book_id,
                error=str(e)
            )
            return False
    
    async def batch_upsert_embeddings(
        self,
        embeddings: List[Dict[str, Any]]
    ) -> bool:
        """
        Batch insert or update book embeddings.
        
        Args:
            embeddings: List of embedding data dictionaries
                       Each should contain: id, vector, payload
        
        Returns:
            True if successful
        """
        try:
            points = [
                PointStruct(
                    id=emb["id"],
                    vector=emb["vector"],
                    payload=emb["payload"]
                )
                for emb in embeddings
            ]
            
            self._client.upsert(
                collection_name=settings.qdrant_collection_name,
                points=points
            )
            
            logger.info("Batch embeddings upserted", count=len(embeddings))
            return True
            
        except Exception as e:
            logger.error("Failed to batch upsert embeddings", error=str(e))
            return False
    
    async def search_similar_books(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar books using vector similarity.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Optional metadata filters
        
        Returns:
            List of similar books with scores
        """
        try:
            # Build filter if provided
            search_filter = None
            if filters:
                search_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                        for key, value in filters.items()
                    ]
                )
            
            # Perform search
            results = self._client.search(
                collection_name=settings.qdrant_collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            similar_books = [
                {
                    "book_id": hit.id,
                    "score": hit.score,
                    "metadata": hit.payload
                }
                for hit in results
            ]
            
            logger.debug(
                "Similar books found",
                count=len(similar_books),
                threshold=score_threshold
            )
            
            return similar_books
            
        except Exception as e:
            logger.error("Failed to search similar books", error=str(e))
            return []
    
    async def get_book_embedding(self, book_id: str) -> Optional[Dict[str, Any]]:
        """
        Get book embedding by ID.
        
        Args:
            book_id: Book identifier
        
        Returns:
            Book embedding data or None
        """
        try:
            result = self._client.retrieve(
                collection_name=settings.qdrant_collection_name,
                ids=[book_id]
            )
            
            if result:
                point = result[0]
                return {
                    "book_id": point.id,
                    "vector": point.vector,
                    "metadata": point.payload
                }
            
            return None
            
        except Exception as e:
            logger.error("Failed to get book embedding", book_id=book_id, error=str(e))
            return None
    
    async def delete_book_embedding(self, book_id: str) -> bool:
        """
        Delete book embedding.
        
        Args:
            book_id: Book identifier
        
        Returns:
            True if successful
        """
        try:
            self._client.delete(
                collection_name=settings.qdrant_collection_name,
                points_selector=models.PointIdsList(
                    points=[book_id]
                )
            )
            
            logger.debug("Book embedding deleted", book_id=book_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete book embedding", book_id=book_id, error=str(e))
            return False
    
    async def count_embeddings(self) -> int:
        """
        Get total count of embeddings in collection.
        
        Returns:
            Number of embeddings
        """
        try:
            collection_info = self._client.get_collection(
                collection_name=settings.qdrant_collection_name
            )
            return collection_info.points_count
            
        except Exception as e:
            logger.error("Failed to count embeddings", error=str(e))
            return 0
    
    async def health_check(self) -> bool:
        """
        Check Vector DB connection health.
        
        Returns:
            True if connection is healthy
        """
        try:
            # Try to get collection info
            self._client.get_collection(settings.qdrant_collection_name)
            logger.debug("Vector DB health check passed")
            return True
        except Exception as e:
            logger.error("Vector DB health check failed", error=str(e))
            return False


class RecommendationCache:
    """
    Cache layer for recommendation queries.
    Reduces vector search load for common queries.
    """
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl: Time to live in seconds
        """
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached recommendations.
        
        Args:
            cache_key: Cache key
        
        Returns:
            Cached recommendations or None
        """
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            # Check if cache is still valid
            from datetime import datetime, timezone
            if (datetime.now(timezone.utc) - cached_data["timestamp"]).seconds < self.ttl:
                logger.debug("Cache hit", cache_key=cache_key)
                return cached_data["data"]
            else:
                # Remove expired cache
                del self._cache[cache_key]
        
        logger.debug("Cache miss", cache_key=cache_key)
        return None
    
    def set(self, cache_key: str, data: List[Dict[str, Any]]) -> None:
        """
        Set cached recommendations.
        
        Args:
            cache_key: Cache key
            data: Recommendations to cache
        """
        from datetime import datetime, timezone
        self._cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now(timezone.utc)
        }
        logger.debug("Cache set", cache_key=cache_key)
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        logger.debug("Cache cleared")


# Global instances
vector_db = VectorDBClient()
recommendation_cache = RecommendationCache()

__all__ = ["VectorDBClient", "vector_db", "RecommendationCache", "recommendation_cache"]