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
            options = ClientOptions(
                schema="public",
                headers={},
                auto_refresh_token=True,
                persist_session=True
            )
            
            self._client = create_client(
                supabase_url=str(settings.supabase_url),
                supabase_key=settings.supabase_service_key,
                options=options
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


# Global instance
supabase_ops = SupabaseOperations()

__all__ = ["SupabaseClient", "SupabaseOperations", "supabase_ops"]