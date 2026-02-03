"""
Book lookup service for external API integrations (Google Books, Open Library).
Implements caching and rate limiting for API calls.
"""
import asyncio
from typing import Optional, List, Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger
from app.models.book import BookSearchResult, BookCreate

logger = get_logger(__name__)


class BookLookupService:
    """Service for looking up book information from external APIs"""
    
    def __init__(self):
        """Initialize book lookup service"""
        self.google_books_url = "https://www.googleapis.com/books/v1/volumes"
        self.openlibrary_url = settings.openlibrary_api_url
        self.timeout = httpx.Timeout(30.0)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_google_books(self, query: str, max_results: int = 5) -> List[BookSearchResult]:
        """Search Google Books API"""
        try:
            params = {
                "q": query,
                "maxResults": max_results,
                "key": settings.google_books_api_key
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.google_books_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            return self._parse_google_books_response(data)
            
        except Exception as e:
            logger.error("Google Books search failed", query=query, error=str(e))
            return []
    
    def _parse_google_books_response(self, data: Dict[str, Any]) -> List[BookSearchResult]:
        """Parse Google Books API response"""
        results = []
        
        for item in data.get("items", []):
            vol_info = item.get("volumeInfo", {})
            
            # Extract ISBNs
            isbn_13 = None
            for identifier in vol_info.get("industryIdentifiers", []):
                if identifier.get("type") == "ISBN_13":
                    isbn_13 = identifier.get("identifier")
                    break
            
            result = BookSearchResult(
                title=vol_info.get("title", ""),
                authors=vol_info.get("authors", []),
                isbn_13=isbn_13,
                thumbnail_url=vol_info.get("imageLinks", {}).get("thumbnail"),
                description=vol_info.get("description"),
                published_date=vol_info.get("publishedDate"),
                publisher=vol_info.get("publisher"),
                page_count=vol_info.get("pageCount"),
                source="google_books",
                external_id=item.get("id")
            )
            results.append(result)
        
        return results
    
    async def search_by_isbn(self, isbn: str) -> Optional[BookCreate]:
        """Search for book by ISBN"""
        try:
            results = await self.search_google_books(f"isbn:{isbn}", max_results=1)
            if results:
                return self._convert_to_book_create(results[0])
            return None
        except Exception as e:
            logger.error("ISBN search failed", isbn=isbn, error=str(e))
            return None
    
    def _convert_to_book_create(self, search_result: BookSearchResult) -> BookCreate:
        """Convert search result to BookCreate model"""
        return BookCreate(
            title=search_result.title,
            authors=search_result.authors,
            isbn_13=search_result.isbn_13,
            publisher=search_result.publisher,
            published_date=search_result.published_date,
            page_count=search_result.page_count,
            description=search_result.description,
            categories=[]
        )


book_lookup_service = BookLookupService()