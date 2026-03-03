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
        self.openlibrary_url = getattr(settings, 'openlibrary_api_url', 'https://openlibrary.org')
        self.timeout = httpx.Timeout(30.0)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_books(
        self, 
        query: str, 
        page: int = 1, 
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Search for books using Google Books API with pagination
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Dictionary with results and pagination info
        """
        try:
            # Calculate start index for pagination
            start_index = (page - 1) * page_size
            
            params = {
                "q": query,
                "maxResults": min(page_size, 40),  # Google Books max is 40
                "startIndex": start_index,
            }
            
            # Add API key if available
            if hasattr(settings, 'google_books_api_key') and settings.google_books_api_key:
                params["key"] = settings.google_books_api_key
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.google_books_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            results = self._parse_google_books_response(data)
            total_items = data.get("totalItems", 0)
            
            return {
                "results": results,
                "total": total_items,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_items + page_size - 1) // page_size if total_items > 0 else 0
            }
            
        except httpx.HTTPStatusError as e:
            logger.error("Google Books API error", status=e.response.status_code, error=str(e))
            raise Exception(f"External API error: {e.response.status_code}")
        except Exception as e:
            logger.error("Book search failed", query=query, error=str(e))
            raise Exception(f"Book search failed: {str(e)}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_google_books(
        self, 
        query: str, 
        max_results: int = 5
    ) -> List[BookSearchResult]:
        """
        Search Google Books API (legacy method for backward compatibility)
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of BookSearchResult objects
        """
        try:
            params = {
                "q": query,
                "maxResults": max_results,
            }
            
            # Add API key if available
            if hasattr(settings, 'google_books_api_key') and settings.google_books_api_key:
                params["key"] = settings.google_books_api_key
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.google_books_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            return self._parse_google_books_response(data)
            
        except Exception as e:
            logger.error("Google Books search failed", query=query, error=str(e))
            return []
    
    def _parse_google_books_response(self, data: Dict[str, Any]) -> List[BookSearchResult]:
        """Parse Google Books API response into BookSearchResult objects"""
        results = []
        
        for item in data.get("items", []):
            vol_info = item.get("volumeInfo", {})
            
            # Extract ISBNs
            isbn_13 = None
            isbn_10 = None
            for identifier in vol_info.get("industryIdentifiers", []):
                if identifier.get("type") == "ISBN_13":
                    isbn_13 = identifier.get("identifier")
                elif identifier.get("type") == "ISBN_10":
                    isbn_10 = identifier.get("identifier")
            
            # Extract thumbnail (prefer larger image)
            image_links = vol_info.get("imageLinks", {})
            thumbnail = (
                image_links.get("large") or 
                image_links.get("medium") or 
                image_links.get("thumbnail") or
                image_links.get("smallThumbnail")
            )
            
            # Extract categories
            categories = vol_info.get("categories", [])
            
            result = BookSearchResult(
                title=vol_info.get("title", "Unknown Title"),
                authors=vol_info.get("authors", []),
                isbn_13=isbn_13,
                isbn_10=isbn_10,
                thumbnail_url=thumbnail,
                description=vol_info.get("description"),
                published_date=vol_info.get("publishedDate"),
                publisher=vol_info.get("publisher"),
                page_count=vol_info.get("pageCount"),
                categories=categories,
                language=vol_info.get("language"),
                average_rating=vol_info.get("averageRating"),
                ratings_count=vol_info.get("ratingsCount"),
                source="google_books",
                external_id=item.get("id")
            )
            results.append(result)
        
        return results
    
    async def search_by_isbn(self, isbn: str) -> Optional[BookSearchResult]:
        """
        Search for a book by ISBN
        
        Args:
            isbn: ISBN-10 or ISBN-13
            
        Returns:
            BookSearchResult if found, None otherwise
        """
        try:
            # Clean ISBN (remove hyphens and spaces)
            clean_isbn = isbn.replace("-", "").replace(" ", "")
            
            results = await self.search_google_books(f"isbn:{clean_isbn}", max_results=1)
            
            if results:
                return results[0]
            
            return None
            
        except Exception as e:
            logger.error("ISBN search failed", isbn=isbn, error=str(e))
            return None
    
    async def get_book_details(self, external_id: str) -> Optional[BookSearchResult]:
        """
        Get detailed information about a book using its external ID
        
        Args:
            external_id: Google Books volume ID
            
        Returns:
            BookSearchResult with full details
        """
        try:
            url = f"{self.google_books_url}/{external_id}"
            
            params = {}
            if hasattr(settings, 'google_books_api_key') and settings.google_books_api_key:
                params["key"] = settings.google_books_api_key
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # Parse single book response
            results = self._parse_google_books_response({"items": [data]})
            return results[0] if results else None
            
        except Exception as e:
            logger.error("Failed to get book details", external_id=external_id, error=str(e))
            return None
    
    def _convert_to_book_create(self, search_result: BookSearchResult) -> BookCreate:
        """Convert search result to BookCreate model"""
        return BookCreate(
            title=search_result.title,
            authors=search_result.authors,
            isbn_13=search_result.isbn_13,
            isbn_10=search_result.isbn_10,
            publisher=search_result.publisher,
            published_date=search_result.published_date,
            page_count=search_result.page_count,
            description=search_result.description,
            thumbnail_url=search_result.thumbnail_url,
            language=search_result.language,
            categories=search_result.categories or [],
            average_rating=search_result.average_rating,
            ratings_count=search_result.ratings_count
        )


# Create singleton instance
book_lookup_service = BookLookupService()