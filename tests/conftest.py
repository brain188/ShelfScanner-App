"""
Pytest configuration and shared fixtures.
Provides common test fixtures, mocks, and utilities.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import tempfile
import os
from datetime import datetime, timedelta, timezone

@pytest.fixture(scope="session", autouse=True)
def mock_supabase_initialization():
    """
    Mock Supabase client initialization to prevent real connections during tests.
    This fixture runs automatically for all tests.
    """
    with patch('app.db.supabase.create_client') as mock_create:
        # Create a comprehensive mock Supabase client
        mock_client = MagicMock()
        
        # Mock table operations
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_client.table.return_value.insert.return_value.execute.return_value.data = []
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
        mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
        
        # Mock auth operations
        mock_client.auth.sign_in_with_password.return_value = MagicMock()
        mock_client.auth.sign_up.return_value = MagicMock()
        
        mock_create.return_value = mock_client
        yield mock_create

from app.main import app
from app.core.security import token_manager

# Event Loop Configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test Client Fixtures
@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Synchronous test client for FastAPI app.
    Use for simple endpoint testing.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous test client for FastAPI app.
    Use for testing async operations and streaming.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# User Fixtures
@pytest.fixture
def user_data() -> Dict[str, Any]:
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "role": "user"
    }


@pytest.fixture
def user_data_premium() -> Dict[str, Any]:
    """Premium user data for testing"""
    return {
        "email": "premium@example.com",
        "password": "PremiumPass123!",
        "full_name": "Premium User",
        "role": "premium"
    }


@pytest.fixture
def admin_user_data() -> Dict[str, Any]:
    """Admin user data for testing"""
    return {
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "full_name": "Admin User",
        "role": "admin"
    }


@pytest.fixture
def mock_user() -> Dict[str, Any]:
    """Mock user object from database"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "is_active": True,
        "is_email_verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }

@pytest.fixture(autouse=True)
def mock_get_user_by_id(mock_user):
    """Auto-mock get_user_by_id for all tests"""
    with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock:
        mock.return_value = mock_user
        yield mock

@pytest.fixture
def inactive_user() -> Dict[str, Any]:
    """Mock inactive user"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "email": "inactive@example.com",
        "full_name": "Inactive User",
        "role": "user",
        "is_active": False,
        "is_email_verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }


@pytest.fixture
def deleted_user() -> Dict[str, Any]:
    """Mock soft-deleted user"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "email": "deleted@example.com",
        "full_name": "Deleted User",
        "role": "user",
        "is_active": False,
        "is_email_verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": datetime.now(timezone.utc).isoformat()
    }


# Authentication Fixtures
@pytest.fixture
def auth_token(mock_user: Dict[str, Any]) -> str:
    """Generate valid JWT token for testing"""
    token_data = {
        "sub": mock_user["id"],
        "email": mock_user["email"],
        "role": mock_user["role"]
    }
    return token_manager.create_access_token(token_data)


@pytest.fixture
def premium_token() -> str:
    """Generate valid JWT token for premium user"""
    token_data = {
        "sub": "premium-user-id",
        "email": "premium@example.com",
        "role": "premium"
    }
    return token_manager.create_access_token(token_data)


@pytest.fixture
def admin_token() -> str:
    """Generate valid JWT token for admin user"""
    token_data = {
        "sub": "admin-user-id",
        "email": "admin@example.com",
        "role": "admin"
    }
    return token_manager.create_access_token(token_data)


@pytest.fixture
def expired_token() -> str:
    """Generate expired JWT token"""
    token_data = {
        "sub": "user-id",
        "email": "user@example.com",
        "role": "user"
    }
    # Token expired 1 hour ago
    expires_delta = timedelta(minutes=-60)
    return token_manager.create_access_token(token_data, expires_delta)


@pytest.fixture
def auth_headers(auth_token: str) -> Dict[str, str]:
    """Authorization headers with valid token"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def premium_headers(premium_token: str) -> Dict[str, str]:
    """Authorization headers with premium token"""
    return {"Authorization": f"Bearer {premium_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> Dict[str, str]:
    """Authorization headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


# Book Fixtures
@pytest.fixture
def book_data() -> Dict[str, Any]:
    """Sample book data"""
    return {
        "title": "The Great Gatsby",
        "subtitle": "A Novel",
        "authors": ["F. Scott Fitzgerald"],
        "isbn_13": "9780743273565",
        "isbn_10": "0743273567",
        "publisher": "Scribner",
        "published_date": "2004-09-30",
        "page_count": 180,
        "language": "en",
        "description": "The story of the mysteriously wealthy Jay Gatsby...",
        "categories": ["Fiction", "Classics"],
        "thumbnail_url": "https://books.google.com/books/content?id=...",
        "average_rating": 4.5,
        "ratings_count": 1000
    }


@pytest.fixture
def mock_book() -> Dict[str, Any]:
    """Mock book object from database"""
    return {
        "id": "book-uuid-1",
        "title": "The Great Gatsby",
        "authors": ["F. Scott Fitzgerald"],
        "isbn_13": "9780743273565",
        "isbn_10": "0743273567",
        "publisher": "Scribner",
        "page_count": 180,
        "thumbnail_url": "https://example.com/thumbnail.jpg",
        "average_rating": 4.5,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def mock_books() -> list:
    """List of mock books"""
    return [
        {
            "id": f"book-uuid-{i}",
            "title": f"Test Book {i}",
            "authors": [f"Author {i}"],
            "isbn_13": f"978000000000{i}",
            "page_count": 200 + (i * 10),
            "average_rating": 4.0 + (i * 0.1),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        for i in range(1, 6)
    ]


@pytest.fixture
def user_book_data() -> Dict[str, Any]:
    """User's book library entry data"""
    return {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "book_id": "book-uuid-1",
        "status": "currently_reading",
        "current_page": 50,
        "rating": 5,
        "review": "Excellent book!",
        "favorite": True
    }


# Scan/OCR Fixtures
@pytest.fixture
def test_image_path() -> Generator[str, None, None]:
    """Create temporary test image file"""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        # Create simple test image (1x1 pixel)
        tmp.write(b'\xff\xd8\xff\xe0\x00\x10JFIF')
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def test_pdf_path() -> Generator[str, None, None]:
    """Create temporary test PDF file"""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        # Minimal PDF content
        tmp.write(b'%PDF-1.4\n%EOF')
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def mock_scan_result() -> Dict[str, Any]:
    """Mock OCR scan result"""
    return {
        "id": "scan-uuid-1",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "scan_type": "image",
        "status": "completed",
        "file_name": "test_image.jpg",
        "file_size": 1024,
        "extracted_texts": [
            {
                "text": "The Great Gatsby",
                "confidence": 95.5,
                "confidence_level": "high"
            }
        ],
        "detected_books": [
            {
                "title": "The Great Gatsby",
                "authors": ["F. Scott Fitzgerald"],
                "isbn": "9780743273565",
                "confidence_score": 0.95
            }
        ],
        "ocr_confidence_avg": 95.5,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def ocr_extracted_text() -> list:
    """Mock OCR extracted text"""
    return [
        {
            "text": "The Great Gatsby",
            "confidence": 95.5,
            "bounding_box": {"x": 10, "y": 20, "width": 150, "height": 30}
        },
        {
            "text": "F. Scott Fitzgerald",
            "confidence": 92.3,
            "bounding_box": {"x": 10, "y": 60, "width": 180, "height": 25}
        }
    ]


# Recommendation Fixtures
@pytest.fixture
def mock_recommendations() -> list:
    """Mock book recommendations"""
    return [
        {
            "book": {
                "id": "rec-book-1",
                "title": "1984",
                "authors": ["George Orwell"],
                "thumbnail_url": "https://example.com/1984.jpg"
            },
            "recommendation_score": 0.92,
            "reason": "Based on your interest in classic literature"
        },
        {
            "book": {
                "id": "rec-book-2",
                "title": "Brave New World",
                "authors": ["Aldous Huxley"],
                "thumbnail_url": "https://example.com/bnw.jpg"
            },
            "recommendation_score": 0.88,
            "reason": "Similar dystopian themes"
        }
    ]


@pytest.fixture
def mock_embeddings() -> list:
    """Mock vector embeddings (384 dimensions)"""
    import numpy as np
    return np.random.rand(384).tolist()


# External API Mocks
@pytest.fixture
def mock_google_books_response():
    """Mock Google Books API response"""
    return {
        "items": [
            {
                "id": "iXn5U2IzVH0C",
                "volumeInfo": {
                    "title": "The Great Gatsby",
                    "authors": ["F. Scott Fitzgerald"],
                    "publishedDate": "2004-09-30",
                    "industryIdentifiers": [
                        {"type": "ISBN_13", "identifier": "9780743273565"},
                        {"type": "ISBN_10", "identifier": "0743273567"}
                    ],
                    "pageCount": 180,
                    "imageLinks": {
                        "thumbnail": "http://books.google.com/books/content?id=..."
                    },
                    "description": "The story of Jay Gatsby..."
                }
            }
        ]
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "choices": [
            {
                "message": {
                    "content": "Based on your reading history, I recommend these books..."
                }
            }
        ],
        "usage": {
            "total_tokens": 150
        }
    }


# Database Mocks
@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    mock = Mock()
    
    # Mock table operations
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock.table.return_value.insert.return_value.execute.return_value.data = []
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
    mock.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
    
    return mock

@pytest.fixture
def mock_ops():
    """
    Mock all database operations in supabase_ops.
    This bypasses the real Supabase client entirely.
    """
    with patch("app.api.v1.auth.supabase_ops", autospec=True) as mock:
        # Default behavior: return empty or None to avoid crashes
        mock.get_user_by_email = AsyncMock(return_value=None)
        mock.create_user = AsyncMock()
        mock.get_user_by_id = AsyncMock()
        mock.update_user = AsyncMock()
        yield mock

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = AsyncMock()
    
    # Mock basic operations
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = False
    mock.expire.return_value = True
    
    return mock


@pytest.fixture
def mock_qdrant():
    """Mock Qdrant client"""
    mock = AsyncMock()
    
    # Mock search operation
    mock.search.return_value = [
        {
            "id": "book-1",
            "score": 0.92,
            "payload": {"title": "Similar Book 1"}
        }
    ]
    
    return mock


# Celery Task Mocks
@pytest.fixture
def mock_celery_task():
    """Mock Celery task"""
    mock = AsyncMock()
    mock.delay.return_value.id = "task-id-123"
    mock.delay.return_value.status = "PENDING"
    return mock


# File Upload Fixtures
@pytest.fixture
def upload_file_image(test_image_path: str):
    """File upload fixture for images"""
    with open(test_image_path, "rb") as f:
        return ("test_image.jpg", f, "image/jpeg")


@pytest.fixture
def upload_file_pdf(test_pdf_path: str):
    """File upload fixture for PDFs"""
    with open(test_pdf_path, "rb") as f:
        return ("test_document.pdf", f, "application/pdf")


# Utility Fixtures
@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing"""
    class MockDateTime:
        @staticmethod
        def utcnow():
            return datetime(2024, 1, 31, 12, 0, 0)
    
    return MockDateTime


@pytest.fixture
def sample_isbn_10() -> str:
    """Sample valid ISBN-10"""
    return "0743273567"


@pytest.fixture
def sample_isbn_13() -> str:
    """Sample valid ISBN-13"""
    return "9780743273565"


@pytest.fixture
def invalid_isbn() -> str:
    """Invalid ISBN for testing validation"""
    return "1234567890"


# Test Database Setup/Teardown
@pytest.fixture(scope="session")
async def test_db():
    """
    Set up test database.
    This would create tables and seed test data.
    """
    # Setup: Create tables, seed data
    # In real scenario, you'd run migrations
    yield
    
    # Teardown: Clean up test data
    # Drop tables or truncate


@pytest.fixture(autouse=True)
def reset_database():
    """
    Reset database state between tests.
    Auto-used for all tests.
    """
    # Before test: Clean slate
    yield
    
    # After test: Cleanup
    # Truncate tables or delete test data


# Environment Variable Mocking
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-characters-long")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GOOGLE_BOOKS_API_KEY", "test-google-books-key")



# Logging Fixtures
@pytest.fixture
def capture_logs(caplog):
    """Capture log output for testing"""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


# Common test data for parametrized tests
VALID_EMAILS = [
    "user@example.com",
    "test.user@example.co.uk",
    "user+tag@example.com"
]

INVALID_EMAILS = [
    "invalid-email",
    "@example.com",
    "user@",
    "user @example.com"
]

VALID_PASSWORDS = [
    "ValidPass123!",
    "Str0ng@Password",
    "Test1234!"
]

INVALID_PASSWORDS = [
    "short",  # Too short
    "nouppercase123!",  # No uppercase
    "NOLOWERCASE123!",  # No lowercase
    "NoDigits!@#",  # No digits
    "NoSpecial123"  # No special char
]

# Export for use in tests
pytest.VALID_EMAILS = VALID_EMAILS
pytest.INVALID_EMAILS = INVALID_EMAILS
pytest.VALID_PASSWORDS = VALID_PASSWORDS
pytest.INVALID_PASSWORDS = INVALID_PASSWORDS