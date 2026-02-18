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

async def get_personalized_recommendations(
    user_id: str,
    limit: int = 10,
    algorithm: str = "hybrid"
) -> Dict[str, Any]:
    """Get personalized recommendations (wrapper for tests)"""
    from app.db.supabase import supabase_ops
    
    try:
        # Get user's books
        library = await supabase_ops.get_user_library(user_id, page=1, page_size=100)
        user_books = library.get("books", [])
        
        # Generate recommendations
        recs = await recommendation_engine.get_recommendations(
            user_id=user_id,
            user_books=user_books,
            limit=limit
        )
        
        return {
            "recommendations": recs,
            "total": len(recs),
            "algorithm": algorithm
        }
    except Exception as e:
        logger.error("Failed to get recommendations", error=str(e))
        return {"recommendations": [], "total": 0}


async def find_similar_books(book: Dict[str, Any], limit: int = 5) -> Dict[str, Any]:
    """Find similar books (wrapper for tests)"""
    similar = await recommendation_engine._find_similar_books(book, limit)
    return {
        "similar_books": similar,
        "search_method": "vector_similarity"
    }

async def generate_recommendation_explanation(
    book_id: str,
    user_books: List[Dict[str, Any]] = None
) -> Dict[str, str]:
    """Generate AI explanation for why a book is recommended"""
    try:
        if not user_books:
            user_books = []
        
        explanation = await recommendation_engine.get_ai_recommendations(
            user_books=user_books,
            preferences=f"Explaining recommendation for book {book_id}"
        )
        
        return {"explanation": explanation}
        
    except Exception as e:
        logger.error("Failed to generate explanation", error=str(e))
        return {"explanation": "This book is recommended based on your reading history."}
    
async def refresh_recommendations(user_id: str) -> Dict[str, str]:
    """Refresh cached recommendations"""
    try:
        cache_key = f"rec_{user_id}_10"
        recommendation_cache._cache.pop(cache_key, None)
        logger.info("Cache cleared", user_id=user_id)
        return {"message": "Recommendations refreshed"}
    except Exception as e:
        logger.error("Failed to refresh", error=str(e))
        return {"message": "Failed to refresh"}
    
recommendation_engine = RecommendationEngine()

__all__ = [
    "RecommendationEngine",
    "recommendation_engine",
    "get_personalized_recommendations",
    "find_similar_books",
    "generate_recommendation_explanation",
    "refresh_recommendations"
]