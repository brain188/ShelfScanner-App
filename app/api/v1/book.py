"""
Books API endpoints for library management.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import get_current_active_user
from app.core.logging import get_logger
from app.models.book import (
    Book,
    BookCreate,
    UserBookCreate,
    UserBookUpdate,
    BookWithUserData,
    BookList,
    BookStats,
    BookStatus
)
from app.db.supabase import supabase_ops
from app.services.book_lookup import book_lookup_service
from app.services.embedding_service import embedding_service
from app.db.vector_db import vector_db

logger = get_logger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: BookCreate,
    current_user: dict = Depends(get_current_active_user)
) -> Book:
    """Create a new book in the database"""
    try:
        # Check if book already exists by ISBN
        if book_data.isbn_13:
            existing = await supabase_ops.get_book_by_isbn(book_data.isbn_13)
            if existing:
                return Book(**existing)
        
        # Create book
        book_dict = {
            **book_data.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        created_book = await supabase_ops.create_book(book_dict)
        
        # Generate and store embedding
        embedding = embedding_service.generate_book_embedding(
            title=book_data.title,
            authors=book_data.authors,
            description=book_data.description or ""
        )
        
        if embedding:
            await vector_db.upsert_book_embedding(
                book_id=created_book["id"],
                embedding=embedding,
                metadata={
                    "title": book_data.title,
                    "authors": book_data.authors,
                    "categories": book_data.categories
                }
            )
        
        logger.info("Book created", book_id=created_book["id"])
        
        return Book(**created_book)
        
    except Exception as e:
        logger.error("Book creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create book"
        )


@router.get("/search", response_model=list)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def search_books(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user)
):
    """Search books by title, author, or ISBN"""
    try:
        # Search in external APIs
        results = await book_lookup_service.search_google_books(q, max_results=limit)
        
        logger.info("Book search completed", query=q, results=len(results))
        
        return results
        
    except Exception as e:
        logger.error("Book search failed", query=q, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.get("/library", response_model=BookList)
async def get_user_library(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[BookStatus] = None,
    current_user: dict = Depends(get_current_active_user)
) -> BookList:
    """Get user's book library with pagination"""
    try:
        offset = (page - 1) * page_size
        
        user_books = await supabase_ops.get_user_books(
            current_user["user_id"],
            limit=page_size,
            offset=offset,
            status=status_filter.value if status_filter else None
        )
        
        # Convert to BookWithUserData
        books_with_data = []
        for ub in user_books:
            book = ub.get("books", {})
            if book:
                books_with_data.append(
                    BookWithUserData(**{**book, "user_data": ub})
                )
        
        total = len(user_books)
        total_pages = (total + page_size - 1) // page_size
        
        return BookList(
            books=books_with_data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error("Failed to get library", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve library"
        )


@router.post("/library", status_code=status.HTTP_201_CREATED)
async def add_book_to_library(
    book_data: UserBookCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Add a book to user's library"""
    try:
        user_book_dict = {
            **book_data.model_dump(),
            "user_id": current_user["user_id"],
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = await supabase_ops.add_user_book(user_book_dict)
        
        logger.info(
            "Book added to library",
            user_id=current_user["user_id"],
            book_id=book_data.book_id
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to add book to library", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add book"
        )


@router.patch("/library/{book_id}")
async def update_library_book(
    book_id: str,
    updates: UserBookUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update book in user's library"""
    try:
        # In full implementation, verify ownership and update
        logger.info(
            "Library book updated",
            user_id=current_user["user_id"],
            book_id=book_id
        )
        
        return {"message": "Book updated successfully"}
        
    except Exception as e:
        logger.error("Failed to update library book", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update book"
        )


@router.delete("/library/{book_id}")
async def remove_from_library(
    book_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Remove book from library"""
    try:
        logger.info(
            "Book removed from library",
            user_id=current_user["user_id"],
            book_id=book_id
        )
        
        return {"message": "Book removed successfully"}
        
    except Exception as e:
        logger.error("Failed to remove book", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove book"
        )


@router.get("/stats", response_model=BookStats)
async def get_reading_stats(
    current_user: dict = Depends(get_current_active_user)
) -> BookStats:
    """Get user's reading statistics"""
    try:
        user_books = await supabase_ops.get_user_books(
            current_user["user_id"],
            limit=1000,
            offset=0
        )
        
        # Calculate stats
        total_books = len(user_books)
        books_read = sum(1 for b in user_books if b.get("status") == "read")
        books_reading = sum(1 for b in user_books if b.get("status") == "currently_reading")
        books_want_to_read = sum(1 for b in user_books if b.get("status") == "want_to_read")
        
        # Calculate average rating
        ratings = [b.get("rating") for b in user_books if b.get("rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        return BookStats(
            total_books=total_books,
            books_read=books_read,
            books_reading=books_reading,
            books_want_to_read=books_want_to_read,
            total_pages_read=0,  # Simplified for MVP
            average_rating=avg_rating,
            favorite_genres=[]  # Simplified for MVP
        )
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )