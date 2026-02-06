"""
Recommendations API endpoints for AI-powered book suggestions.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import get_current_active_user
from app.core.logging import get_logger
from app.db.supabase import supabase_ops
from app.services.recommendation_engine import recommendation_engine
from app.services.embedding_service import embedding_service
from app.db.vector_db import vector_db

logger = get_logger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_recommendations(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get personalized book recommendations based on user's library.
    """
    try:
        # Get user's books
        user_books = await supabase_ops.get_user_books(
            current_user["user_id"],
            limit=100,
            offset=0
        )
        
        if not user_books:
            return {
                "recommendations": [],
                "message": "Add some books to your library to get personalized recommendations"
            }
        
        # Get recommendations
        recommendations = await recommendation_engine.get_recommendations(
            user_id=current_user["user_id"],
            user_books=user_books,
            limit=limit
        )
        
        logger.info(
            "Recommendations generated",
            user_id=current_user["user_id"],
            count=len(recommendations)
        )
        
        return {
            "recommendations": recommendations,
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error("Failed to generate recommendations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


@router.get("/similar/{book_id}")
async def get_similar_books(
    book_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get books similar to a specific book.
    """
    try:
        # Get book details
        book = await supabase_ops.get_book_by_id(book_id)
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Generate embedding for the book
        embedding = embedding_service.generate_book_embedding(
            title=book.get("title", ""),
            authors=book.get("authors", []),
            description=book.get("description", "")
        )
        
        if not embedding:
            return {"similar_books": [], "count": 0}
        
        # Search for similar books
        similar_books = await vector_db.search_similar_books(
            query_vector=embedding,
            limit=limit + 1,  # +1 because the book itself might be included
            score_threshold=0.7
        )
        
        # Remove the query book itself
        similar_books = [b for b in similar_books if b["book_id"] != book_id][:limit]
        
        logger.info(
            "Similar books found",
            book_id=book_id,
            count=len(similar_books)
        )
        
        return {
            "similar_books": similar_books,
            "count": len(similar_books)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to find similar books", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar books"
        )


@router.get("/ai-explanation")
@limiter.limit("10/hour")
async def get_ai_explanation(
    request: Request,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get AI-generated explanation for recommendations.
    Rate limited due to LLM cost.
    """
    try:
        # Get user's books
        user_books = await supabase_ops.get_user_books(
            current_user["user_id"],
            limit=20,
            offset=0
        )
        
        if not user_books:
            return {
                "explanation": "Add books to your library to receive personalized AI recommendations!"
            }
        
        # Get AI explanation
        explanation = await recommendation_engine.get_ai_recommendations(
            user_books=user_books
        )
        
        logger.info("AI explanation generated", user_id=current_user["user_id"])
        
        return {
            "explanation": explanation
        }
        
    except Exception as e:
        logger.error("Failed to generate AI explanation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation"
        )


@router.post("/refresh")
async def refresh_recommendations(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Clear recommendation cache to force refresh.
    """
    try:
        from app.db.vector_db import recommendation_cache
        
        # Clear cache for this user
        cache_key = f"rec_{current_user['user_id']}_10"
        recommendation_cache._cache.pop(cache_key, None)
        
        logger.info("Recommendation cache cleared", user_id=current_user["user_id"])
        
        return {"message": "Recommendations will be refreshed on next request"}
        
    except Exception as e:
        logger.error("Failed to refresh recommendations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh recommendations"
        )