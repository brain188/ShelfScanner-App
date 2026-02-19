"""
Supabase client and database operations.
Implements connection pooling and error handling.
"""
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SupabaseClient:
    """
    Supabase client wrapper with connection management.
    Implements singleton pattern for client reuse.
    """
    
    _instance: Optional["SupabaseClient"] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase client"""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client with configuration"""
        try:
            # options = ClientOptions(
            #     schema="public",
            #     headers={},
            #     auto_refresh_token=True,
            #     persist_session=True
            # )
            
            self._client = create_client(
                supabase_url=str(settings.supabase_url),
                supabase_key=settings.supabase_service_key,
                # options=options
            )
            
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Supabase client", error=str(e))
            raise
    
    @property
    def client(self) -> Client:
        """Get Supabase client instance"""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    async def health_check(self) -> bool:
        """
        Check Supabase connection health.
        
        Returns:
            True if connection is healthy
        """
        try:
            # Simple query to test connection
            response = self._client.table("users").select("count", count="exact").limit(0).execute()
            logger.debug("Supabase health check passed", response=response.data)
            return True
        except Exception as e:
            logger.error("Supabase health check failed", error=str(e))
            return False


class SupabaseOperations:
    """
    High-level Supabase database operations.
    Provides abstraction over Supabase client.
    """
    
    def __init__(self):
        """Initialize operations with client"""
        self.db = SupabaseClient()
    
    # User Operations
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            user_data: User data dictionary
        
        Returns:
            Created user data
        """
        try:
            response = self.db.client.table("users").insert(user_data).execute()
            logger.info("User created", user_id=response.data[0]["id"])
            return response.data[0]
        except Exception as e:
            logger.error("Failed to create user", error=str(e))
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
        
        Returns:
            User data or None
        """
        try:
            response = self.db.client.table("users").select("*").eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to get user", user_id=user_id, error=str(e))
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.
        
        Args:
            email: User email
        
        Returns:
            User data or None
        """
        try:
            response = self.db.client.table("users").select("*").eq("email", email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to get user by email", email=email, error=str(e))
            return None
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user data.
        
        Args:
            user_id: User ID
            user_data: Updated user data
        
        Returns:
            Updated user data
        """
        try:
            response = self.db.client.table("users").update(user_data).eq("id", user_id).execute()
            logger.info("User updated", user_id=user_id)
            return response.data[0]
        except Exception as e:
            logger.error("Failed to update user", user_id=user_id, error=str(e))
            raise
    
    async def update_user_last_login(self, user_id: str) -> None:
        """
        Update user's last_login timestamp.
        This is called on each successful authentication.
        Non-critical operation - failures are logged but not raised.
        
        Args:
            user_id: User ID to update
        """
        try:
            from datetime import datetime, timezone
            
            self.db.client.table("users").update({
                "last_login": datetime.now(timezone.utc).isoformat()
            }).eq("id", user_id).execute()
            
            logger.debug("Updated last_login", user_id=user_id)
        except Exception as e:
            # Don't raise - this is non-critical
            logger.warning("Failed to update last_login", user_id=user_id, error=str(e))
    
    # Book Operations
    
    async def create_book(self, book_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new book.
        
        Args:
            book_data: Book data dictionary
        
        Returns:
            Created book data
        """
        try:
            response = self.db.client.table("books").insert(book_data).execute()
            logger.info("Book created", book_id=response.data[0]["id"])
            return response.data[0]
        except Exception as e:
            logger.error("Failed to create book", error=str(e))
            raise
    
    async def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """
        Get book by ID.
        
        Args:
            book_id: Book ID
        
        Returns:
            Book data or None
        """
        try:
            response = self.db.client.table("books").select("*").eq("id", book_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to get book", book_id=book_id, error=str(e))
            return None
    
    async def get_book_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """
        Get book by ISBN.
        
        Args:
            isbn: Book ISBN (10 or 13)
        
        Returns:
            Book data or None
        """
        try:
            response = (
                self.db.client.table("books")
                .select("*")
                .or_(f"isbn_10.eq.{isbn},isbn_13.eq.{isbn}")
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to get book by ISBN", isbn=isbn, error=str(e))
            return None
    
    async def search_books(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search books by title or author.
        
        Args:
            query: Search query
            limit: Maximum results
            offset: Result offset for pagination
        
        Returns:
            List of matching books
        """
        try:
            response = (
                self.db.client.table("books")
                .select("*")
                .or_(f"title.ilike.%{query}%,authors.cs.{{{query}}}")
                .range(offset, offset + limit - 1)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error("Failed to search books", query=query, error=str(e))
            return []
    
    # User Book Operations
    
    async def add_user_book(self, user_book_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add book to user's library.
        
        Args:
            user_book_data: User book data
        
        Returns:
            Created user book data
        """
        try:
            response = self.db.client.table("user_books").insert(user_book_data).execute()
            logger.info(
                "Book added to user library",
                user_id=user_book_data["user_id"],
                book_id=user_book_data["book_id"]
            )
            return response.data[0]
        except Exception as e:
            logger.error("Failed to add user book", error=str(e))
            raise
    
    async def get_user_books(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's books with optional filtering.
        
        Args:
            user_id: User ID
            limit: Maximum results
            offset: Result offset
            status: Optional status filter
        
        Returns:
            List of user's books
        """
        try:
            query = (
                self.db.client.table("user_books")
                .select("*, books(*)")
                .eq("user_id", user_id)
            )
            
            if status:
                query = query.eq("status", status)
            
            response = query.range(offset, offset + limit - 1).execute()
            return response.data
        except Exception as e:
            logger.error("Failed to get user books", user_id=user_id, error=str(e))
            return []
    
    async def update_user_book(
        self,
        user_id: str,
        book_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user's book in library.
        
        Args:
            user_id: User ID
            book_id: Book ID
            updates: Fields to update
        
        Returns:
            Updated user book data
        
        Raises:
            Exception: If update fails
        """
        try:
            from datetime import datetime, timezone
            
            # Add updated timestamp
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            response = (
                self.db.client.table("user_books")
                .update(updates)
                .eq("user_id", user_id)
                .eq("book_id", book_id)
                .execute()
            )
            
            if not response.data:
                raise Exception("Book not found in user's library")
            
            logger.info(
                "User book updated",
                user_id=user_id,
                book_id=book_id
            )
            
            return response.data[0]
            
        except Exception as e:
            logger.error(
                "Failed to update user book",
                user_id=user_id,
                book_id=book_id,
                error=str(e)
            )
            raise


    async def remove_book_from_library(
        self,
        user_id: str,
        book_id: str
    ) -> bool:
        """
        Remove book from user's library.
        
        Args:
            user_id: User ID
            book_id: Book ID
        
        Returns:
            True if removed, False if not found
        """
        try:
            response = (
                self.db.client.table("user_books")
                .delete()
                .eq("user_id", user_id)
                .eq("book_id", book_id)
                .execute()
            )
            
            removed = len(response.data) > 0
            
            if removed:
                logger.info(
                    "Book removed from library",
                    user_id=user_id,
                    book_id=book_id
                )
            else:
                logger.warning(
                    "Book not found in library",
                    user_id=user_id,
                    book_id=book_id
                )
            
            return removed
            
        except Exception as e:
            logger.error(
                "Failed to remove book from library",
                user_id=user_id,
                book_id=book_id,
                error=str(e)
            )
            return False


    async def get_reading_statistics(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get user's reading statistics.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with reading stats:
            - total_books: Total books in library
            - books_read: Number of books read
            - books_reading: Number of books currently reading
            - books_want_to_read: Number of books want to read
            - total_pages_read: Total pages read
            - average_rating: Average rating given
            - favorite_genres: List of favorite genres (top 5)
        """
        try:
            # Get all user books
            user_books = await self.get_user_books(
                user_id=user_id,
                limit=1000,  # Get all books
                offset=0
            )
            
            # Calculate statistics
            total_books = len(user_books)
            books_read = sum(
                1 for book in user_books 
                if book.get("status") == "read"
            )
            books_reading = sum(
                1 for book in user_books 
                if book.get("status") == "currently_reading"
            )
            books_want_to_read = sum(
                1 for book in user_books 
                if book.get("status") == "want_to_read"
            )
            
            # Calculate total pages read
            total_pages_read = 0
            for book in user_books:
                if book.get("status") == "read":
                    # Get page count from nested books data
                    book_data = book.get("books", {})
                    page_count = book_data.get("page_count", 0)
                    if page_count:
                        total_pages_read += page_count
            
            # Calculate average rating (only for rated books)
            ratings = [
                book.get("rating") 
                for book in user_books 
                if book.get("rating") is not None
            ]
            average_rating = (
                round(sum(ratings) / len(ratings), 2) 
                if ratings 
                else None
            )
            
            # Get favorite genres (top 5 most common categories)
            genre_counts = {}
            for book in user_books:
                book_data = book.get("books", {})
                categories = book_data.get("categories", [])
                for category in categories:
                    if category:
                        genre_counts[category] = genre_counts.get(category, 0) + 1
            
            # Sort by count and get top 5
            favorite_genres = sorted(
                genre_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            favorite_genres = [genre for genre, _ in favorite_genres]
            
            stats = {
                "total_books": total_books,
                "books_read": books_read,
                "books_reading": books_reading,
                "books_want_to_read": books_want_to_read,
                "total_pages_read": total_pages_read,
                "average_rating": average_rating,
                "favorite_genres": favorite_genres
            }
            
            logger.info("Reading statistics calculated", user_id=user_id)
            
            return stats
            
        except Exception as e:
            logger.error(
                "Failed to get reading statistics",
                user_id=user_id,
                error=str(e)
            )
            # Return empty stats on error
            return {
                "total_books": 0,
                "books_read": 0,
                "books_reading": 0,
                "books_want_to_read": 0,
                "total_pages_read": 0,
                "average_rating": None,
                "favorite_genres": []
            }


    async def get_user_library(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's library with pagination and filtering.
        
        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Items per page
            status_filter: Optional status filter
        
        Returns:
            Dictionary with books, pagination info
        """
        try:
            offset = (page - 1) * page_size
            
            # Build query
            query = (
                self.db.client.table("user_books")
                .select("*, books(*)", count="exact")
                .eq("user_id", user_id)
            )
            
            if status_filter:
                query = query.eq("status", status_filter)
            
            # Get total count first
            count_response = await self.get_user_books(
                user_id=user_id,
                limit=10000,  # Large number to get all
                offset=0,
                status=status_filter
            )
            total = len(count_response)
            
            # Get paginated results
            user_books = await self.get_user_books(
                user_id=user_id,
                limit=page_size,
                offset=offset,
                status=status_filter
            )
            
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            return {
                "books": user_books,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(
                "Failed to get user library",
                user_id=user_id,
                error=str(e)
            )
            return {
                "books": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }

    async def add_book_to_library(
        self,
        user_id: str,
        book_id: str,
        status: str = "want_to_read",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add book to user's library.
        Alias for add_user_book with better naming.
        
        Args:
            user_id: User ID
            book_id: Book ID
            status: Reading status
            **kwargs: Additional book data (rating, notes, etc.)
        
        Returns:
            Created user book entry
        """
        from datetime import datetime, timezone
        
        user_book_data = {
            "user_id": user_id,
            "book_id": book_id,
            "status": status,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
        
        return await self.add_user_book(user_book_data)

    # Scan Operations   
    async def create_scan_result(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create scan result.
        
        Args:
            scan_data: Scan result data
        
        Returns:
            Created scan result
        """
        try:
            response = self.db.client.table("scan_results").insert(scan_data).execute()
            logger.info("Scan result created", scan_id=response.data[0]["id"])
            return response.data[0]
        except Exception as e:
            logger.error("Failed to create scan result", error=str(e))
            raise
    
    async def update_scan_result(
        self,
        scan_id: str,
        scan_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update scan result.
        
        Args:
            scan_id: Scan ID
            scan_data: Updated scan data
        
        Returns:
            Updated scan result
        """
        try:
            response = (
                self.db.client.table("scan_results")
                .update(scan_data)
                .eq("id", scan_id)
                .execute()
            )
            logger.info("Scan result updated", scan_id=scan_id)
            return response.data[0]
        except Exception as e:
            logger.error("Failed to update scan result", scan_id=scan_id, error=str(e))
            raise
    
    async def get_user_scans(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's scan history.
        
        Args:
            user_id: User ID
            limit: Maximum results
            offset: Result offset
        
        Returns:
            List of user's scans
        """
        try:
            response = (
                self.db.client.table("scan_results")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error("Failed to get user scans", user_id=user_id, error=str(e))
            return []
        
    async def update_recommendation_interaction(self, user_id: str, rec_id: str, action: str) -> bool:
        """Track recommendation interactions"""
        try:
            # Log the interaction (implement actual tracking if needed)
            logger.info("Recommendation interaction", user_id=user_id, rec_id=rec_id, action=action)
            return True
        except Exception as e:
            logger.error("Failed to track interaction", error=str(e))
            return False

    async def soft_delete_user(self, user_id: str) -> bool:
        """
        Soft delete a user account by setting deleted_at timestamp.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime, timezone
            
            response = (
                self.db.client.table("users")
                .update({
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })
                .eq("user_id", user_id)
                .execute()
            )
            
            if response.data:
                logger.info("User soft deleted successfully", user_id=user_id)
                return True
            else:
                logger.warning("User not found for deletion", user_id=user_id)
                return False
                
        except Exception as e:
            logger.error("Failed to soft delete user", error=str(e), user_id=user_id)
            return False

# Global instance
supabase_client = SupabaseClient()
supabase_ops = SupabaseOperations()

__all__ = ["SupabaseClient", "SupabaseOperations", "supabase_ops"]