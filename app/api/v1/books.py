"""
Books API endpoints for library management.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
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
    BookList,
    BookStats,
    BookStatus,
    BookSearchResult,
    BookSearchResponse
)
from app.db.supabase import supabase_ops
from app.services.book_lookup import book_lookup_service
from app.services.embedding_service import embedding_service
from app.db.vector_db import vector_db

logger = get_logger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def _paginated_response(books, total, page, page_size):
    """Return a plain dict with books + pagination key expected by tests."""
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "books": books,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total": total,
        },
    }

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


@router.get("/search", response_model=BookSearchResponse)
async def search_books(
    query: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user)
) -> BookSearchResponse:
    """Search for books using external APIs"""
    try:
        # # Validate query length
        # if len(query.strip()) < 1:
        #     raise HTTPException(
        #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        #         detail="Query must be at least 1 character long"
        #     )
        
        # Search using book lookup service
        search_results = await book_lookup_service.search_books(
            query=query,
            page=page,
            page_size=page_size
        )
        
        logger.info(
            "Book search completed",
            query=query,
            results_count=len(search_results["results"])
        )
        
        results = search_results.get("results", [])
        total = search_results.get("total", search_results.get("total_results", 0))
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return BookSearchResponse(
            results=results,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Book search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search books"
        )


@router.get("/search/isbn/{isbn}", response_model=BookSearchResult)
async def search_by_isbn(
    isbn: str,
    current_user: dict = Depends(get_current_active_user)
) -> BookSearchResult:
    """Search for a book by ISBN"""
    try:
        result = await book_lookup_service.search_by_isbn(isbn)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ISBN search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search by ISBN"
        )


@router.get("/library")
async def get_user_library(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[BookStatus] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_active_user)
) -> BookList:
    """Get user's book library with pagination"""
    try:
        
        library_data = await supabase_ops.get_user_library(
            user_id = current_user["user_id"],
            page = page,
            page_size = page_size,
            status_filter = status_filter.value if status_filter else None
        )

        raw_books = library_data.get("books", [])
        total = library_data.get("total", len(raw_books))
        
        # Build books list
        book_out = []
        for ub in raw_books:
            nested = ub.get("books")
            if nested and isinstance(nested, dict):
                book_out.append({
                    **nested,
                    "user_data": ub})
            else:
                book_out.append(ub)

        return _paginated_response(book_out, total, page, page_size)    
            
        
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

    book = await supabase_ops.get_book_by_id(book_data.book_id)
    try:
        result = await supabase_ops.add_book_to_library(
            user_id=current_user["user_id"],
            book_id=book_data.book_id,
            status=book_data.status.value,
            rating=book_data.rating,
            review=book_data.review,
            notes=book_data.notes,
            favorite=book_data.favorite
        )

        logger.info(
            "Book added to library",
            user_id=current_user["user_id"],
            book_id=book_data.book_id
        )
        return result

    except Exception as e:
        error_msg = str(e).lower()
        if "already" in error_msg or "duplicate" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Book already in library"
            )
        if book is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        if "not found" in error_msg or "foreign key" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
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
        result = await supabase_ops.update_user_book(
            user_id = current_user["user_id"],
            book_id = book_id,
            updates = updates.model_dump(exclude_none=True)
        )
        logger.info(
            "Library book updated",
            user_id=current_user["user_id"],
            book_id=book_id
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to update library book", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update book"
        )


@router.delete("/library/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_library(
    book_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Remove book from library"""
    try:
        # Call the removed method,
        removed = await supabase_ops.remove_book_from_library(
            current_user["user_id"],
            book_id
        )
    
        # If not removed (not found)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found in library"
            )
        
        logger.info(
            "Book removed from library",
            user_id=current_user["user_id"],
            book_id=book_id
        )
        
        return None
    
    except HTTPException:
        raise
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
        stats = await supabase_ops.get_reading_statistics(current_user["user_id"])
        
        return BookStats(
            total_books=stats["total_books"],
            books_read=stats["books_read"],
            books_reading=stats["books_reading"],
            books_want_to_read=stats.get("books_want_to_read", 0),
            total_pages_read=stats.get("total_pages_read", 0),
            average_rating=stats.get("average_rating", 0), 
            favorite_genres=stats.get("favorite_genres", []),  
        )
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

@router.get("/isbn/{isbn}", response_model=Book)
async def get_book_by_isbn(
    isbn: str,
    current_user: dict = Depends(get_current_active_user)
) -> Book:
    """Get book by ISBN"""
    try:
        book = await supabase_ops.get_book_by_isbn(isbn)
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        return Book(**book)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get book", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve book"
        )

@router.get("/{book_id}", response_model=Book)
async def get_book_by_id(
    book_id: str,
    current_user: dict = Depends(get_current_active_user)
) -> Book:
    """Get book by ID"""
    try:
        book = await supabase_ops.get_book_by_id(book_id)
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        return Book(**book)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get book", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve book"
        )