"""
Book data models and schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, field_validator
from enum import Enum


class BookStatus(str, Enum):
    """Book status in user's library"""
    WANT_TO_READ = "want_to_read"
    CURRENTLY_READING = "currently_reading"
    READ = "read"
    DNF = "did_not_finish"


class ReadingProgress(str, Enum):
    """Reading progress status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class BookBase(BaseModel):
    """Base book model"""
    title: str = Field(..., description="Book title")
    authors: List[str] = Field(default_factory=list, description="Book authors")
    isbn_10: Optional[str] = Field(None, description="ISBN-10")
    isbn_13: Optional[str] = Field(None, description="ISBN-13")
    publisher: Optional[str] = Field(None, description="Publisher")
    published_date: Optional[str] = Field(None, description="Publication date")
    page_count: Optional[int] = Field(None, description="Number of pages")
    language: Optional[str] = Field(None, description="Book language")
    description: Optional[str] = Field(None, description="Book description")
    categories: List[str] = Field(default_factory=list, description="Book categories/genres")
    
    class ConfigDict:
        from_attributes = True


class BookCreate(BookBase):
    """Book creation model"""
    pass


class Book(BookBase):
    """Complete book model"""
    id: str = Field(..., description="Book ID")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="Book cover thumbnail URL")
    google_books_id: Optional[str] = Field(None, description="Google Books ID")
    openlibrary_id: Optional[str] = Field(None, description="Open Library ID")
    average_rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    ratings_count: Optional[int] = Field(None, ge=0, description="Number of ratings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    
    class ConfigDict:
        from_attributes = True


class UserBook(BaseModel):
    """User's book with personal metadata"""
    user_id: str = Field(..., description="User ID")
    book_id: str = Field(..., description="Book ID")
    status: BookStatus = Field(..., description="Reading status")
    progress: ReadingProgress = Field(default=ReadingProgress.NOT_STARTED)
    current_page: Optional[int] = Field(None, ge=0, description="Current page")
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating (1-5)")
    review: Optional[str] = Field(None, description="User review")
    notes: Optional[str] = Field(None, description="User notes")
    favorite: bool = Field(default=False, description="Whether book is favorited")
    added_at: datetime = Field(..., description="Date added to library")
    started_reading_at: Optional[datetime] = Field(None, description="Date started reading")
    finished_reading_at: Optional[datetime] = Field(None, description="Date finished reading")
    
    @field_validator("current_page")
    def validate_current_page(cls, v, values):
        """Validate current page doesn't exceed page count"""
        if v is not None and "page_count" in values and values["page_count"]:
            if v > values["page_count"]:
                raise ValueError("Current page cannot exceed total pages")
        return v
    
    class ConfigDict:
        from_attributes = True


class UserBookCreate(BaseModel):
    """Create user book entry"""
    book_id: str = Field(..., description="Book ID")
    status: BookStatus = Field(default=BookStatus.WANT_TO_READ)
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = None
    notes: Optional[str] = None
    favorite: bool = False


class UserBookUpdate(BaseModel):
    """Update user book entry"""
    status: Optional[BookStatus] = None
    current_page: Optional[int] = Field(None, ge=0)
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = None
    notes: Optional[str] = None
    favorite: Optional[bool] = None


class BookWithUserData(Book):
    """Book with user-specific data"""
    user_data: Optional[UserBook] = None


class BookSearchResult(BaseModel):
    """Book search result from external API"""
    title: str
    authors: List[str]
    isbn_13: Optional[str]
    isbn_10: Optional[str]
    thumbnail_url: Optional[str]
    description: Optional[str]
    published_date: Optional[str]
    publisher: Optional[str]
    page_count: Optional[int]
    categories: List[str] = Field(default_factory=list)   
    language: Optional[str] = None         
    average_rating: Optional[float] = None 
    ratings_count: Optional[int] = None    
    source: str = Field(..., description="Source API (google_books, openlibrary)")
    external_id: str = Field(..., description="External API ID")


class BookList(BaseModel):
    """Paginated book list"""
    books: List[BookWithUserData]
    total: int
    page: int
    page_size: int
    total_pages: int

    @property
    def pagination(self) -> dict:
        """Return pagination metadata"""
        return {
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages
        }
    
    def model_dump(self, **kwargs):
        """Override model_dump to include pagination metadata"""
        data = super().model_dump(**kwargs)
        data["pagination"] = self.pagination
        return data


class BookStats(BaseModel):
    """User's reading statistics"""
    total_books: int
    books_read: int
    books_reading: int
    books_want_to_read: int
    total_pages_read: int
    average_rating: Optional[float]
    favorite_genres: List[str]

class BookSearchResponse(BaseModel):
    """Response model for book search"""
    results: List[BookSearchResult]
    total: int
    page: int
    page_size: int
    total_pages: int