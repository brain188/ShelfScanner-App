"""
Recommendation engine for personalized book recommendations.
"""
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.db.vector_db import vector_db, recommendation_cache
from app.services.embedding_service import embedding_service

logger = get_logger(__name__)


class RecommendationEngine:
    """AI-powered recommendation engine"""
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def get_recommendations(
        self,
        user_id: str,
        user_books: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations for user"""
        try:
            # Check cache
            cache_key = f"rec_{user_id}_{limit}"
            cached = recommendation_cache.get(cache_key)
            if cached:
                return cached
            
            # Get user's favorite books
            favorite_books = [b for b in user_books if b.get("favorite")]
            read_books = [b for b in user_books if b.get("status") == "read" and b.get("rating", 0) >= 4]
            
            # Combine favorites and highly rated
            source_books = favorite_books + read_books
            if not source_books:
                source_books = user_books[:5]  # Use first 5 if no favorites
            
            # Generate recommendations based on similar books
            recommendations = []
            for book in source_books[:3]:  # Use top 3 as seeds
                similar = await self._find_similar_books(book, limit=5)
                recommendations.extend(similar)
            
            # Remove duplicates and books user already has
            user_book_ids = {b["book_id"] for b in user_books}
            unique_recs = []
            seen = set()
            
            for rec in recommendations:
                if rec["book_id"] not in user_book_ids and rec["book_id"] not in seen:
                    unique_recs.append(rec)
                    seen.add(rec["book_id"])
                    
                if len(unique_recs) >= limit:
                    break
            
            # Cache results
            recommendation_cache.set(cache_key, unique_recs)
            
            logger.info("Recommendations generated", user_id=user_id, count=len(unique_recs))
            return unique_recs
            
        except Exception as e:
            logger.error("Failed to generate recommendations", user_id=user_id, error=str(e))
            return []
    
    async def _find_similar_books(self, book: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Find books similar to given book"""
        try:
            # Generate embedding for book
            embedding = embedding_service.generate_book_embedding(
                title=book.get("title", ""),
                authors=book.get("authors", []),
                description=book.get("description", "")
            )
            
            if not embedding:
                return []
            
            # Search for similar books
            similar_books = await vector_db.search_similar_books(
                query_vector=embedding,
                limit=limit,
                score_threshold=0.7
            )
            
            return similar_books
            
        except Exception as e:
            logger.error("Failed to find similar books", error=str(e))
            return []
    
    async def get_ai_recommendations(
        self,
        user_books: List[Dict[str, Any]],
        preferences: Optional[str] = None
    ) -> str:
        """Get AI-generated recommendation explanation"""
        try:
            # Prepare context
            books_summary = "\n".join([
                f"- {b['title']} by {', '.join(b.get('authors', []))}"
                for b in user_books[:10]
            ])
            
            prompt = f"""Based on these books the user has read:
{books_summary}

{f'User preferences: {preferences}' if preferences else ''}

Provide 5 personalized book recommendations with brief explanations."""
            
            response = await self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": "You are a knowledgeable book recommendation assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Failed to get AI recommendations", error=str(e))
            return "Unable to generate recommendations at this time."


recommendation_engine = RecommendationEngine()