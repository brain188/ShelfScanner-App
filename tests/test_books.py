"""
Tests for book-related endpoints.
Tests book search, library management, and book details.
"""
import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock


class TestBookSearch:
    """Test book search functionality"""
    
    def test_search_books_success(self, client, auth_headers, mock_google_books_response):
        """Test successful book search"""
        with patch('app.services.book_service.search_books_external') as mock_search:
            mock_search.return_value = {
                "results": [
                    {
                        "title": "The Great Gatsby",
                        "authors": ["F. Scott Fitzgerald"],
                        "isbn_13": "9780743273565"
                    }
                ],
                "total_results": 1
            }
            
            response = client.get(
                "/api/v1/books/search?q=gatsby",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
        assert data["results"][0]["title"] == "The Great Gatsby"
    
    def test_search_books_empty_query(self, client, auth_headers):
        """Test search with empty query"""
        response = client.get(
            "/api/v1/books/search?q=",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_search_books_min_length(self, client, auth_headers):
        """Test search query minimum length"""
        response = client.get(
            "/api/v1/books/search?q=a",  # Too short
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_search_books_pagination(self, client, auth_headers):
        """Test search with pagination parameters"""
        response = client.get(
            "/api/v1/books/search?q=python&limit=20",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_books_by_isbn(self, client, auth_headers, sample_isbn_13):
        """Test search by ISBN"""
        with patch('app.services.book_service.search_by_isbn') as mock_search:
            mock_search.return_value = {
                "title": "The Great Gatsby",
                "isbn_13": sample_isbn_13
            }
            
            response = client.get(
                f"/api/v1/books/search?q={sample_isbn_13}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_books_no_results(self, client, auth_headers):
        """Test search with no results"""
        with patch('app.services.book_service.search_books_external') as mock_search:
            mock_search.return_value = {
                "results": [],
                "total_results": 0
            }
            
            response = client.get(
                "/api/v1/books/search?q=nonexistentbook12345xyz",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["results"] == []
    
    def test_search_books_external_api_failure(self, client, auth_headers):
        """Test search when external API fails"""
        with patch('app.services.book_service.search_books_external') as mock_search:
            mock_search.side_effect = Exception("API Error")
            
            response = client.get(
                "/api/v1/books/search?q=gatsby",
                headers=auth_headers
            )
        
        assert response.status_code in [500, 502, 503]


class TestGetBookDetails:
    """Test getting book details"""
    
    def test_get_book_by_id_success(self, client, auth_headers, mock_book):
        """Test getting book details by ID"""
        with patch('app.db.supabase.supabase_ops.get_book_by_id') as mock_get:
            mock_get.return_value = mock_book
            
            response = client.get(
                f"/api/v1/books/{mock_book['id']}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == mock_book["id"]
        assert data["title"] == mock_book["title"]
    
    def test_get_book_not_found(self, client, auth_headers):
        """Test getting non-existent book"""
        with patch('app.db.supabase.supabase_ops.get_book_by_id') as mock_get:
            mock_get.return_value = None
            
            response = client.get(
                "/api/v1/books/nonexistent-id",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_book_by_isbn(self, client, auth_headers, sample_isbn_13, mock_book):
        """Test getting book by ISBN"""
        with patch('app.db.supabase.supabase_ops.get_book_by_isbn') as mock_get:
            mock_get.return_value = mock_book
            
            response = client.get(
                f"/api/v1/books/isbn/{sample_isbn_13}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK


class TestUserLibrary:
    """Test user library management"""
    
    def test_get_library_success(self, client, auth_headers, mock_user, mock_books):
        """Test getting user's library"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.get_user_library') as mock_get_lib:
            
            mock_get_user.return_value = mock_user
            mock_get_lib.return_value = {
                "books": mock_books,
                "total": len(mock_books)
            }
            
            response = client.get("/api/v1/books/library", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "books" in data
        assert len(data["books"]) == len(mock_books)
    
    def test_get_library_empty(self, client, auth_headers, mock_user):
        """Test getting empty library"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.get_user_library') as mock_get_lib:
            
            mock_get_user.return_value = mock_user
            mock_get_lib.return_value = {
                "books": [],
                "total": 0
            }
            
            response = client.get("/api/v1/books/library", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["books"] == []
    
    def test_get_library_filtered_by_status(self, client, auth_headers, mock_user):
        """Test filtering library by reading status"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.get_user_library') as mock_get_lib:
            
            mock_get_user.return_value = mock_user
            mock_get_lib.return_value = {
                "books": [],
                "total": 0
            }
            
            response = client.get(
                "/api/v1/books/library?status=currently_reading",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_library_pagination(self, client, auth_headers, mock_user, mock_books):
        """Test library pagination"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.get_user_library') as mock_get_lib:
            
            mock_get_user.return_value = mock_user
            mock_get_lib.return_value = {
                "books": mock_books[:2],
                "total": len(mock_books)
            }
            
            response = client.get(
                "/api/v1/books/library?page=1&page_size=2",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 2


class TestAddBookToLibrary:
    """Test adding books to user library"""
    
    def test_add_book_success(self, client, auth_headers, mock_user, mock_book):
        """Test successfully adding book to library"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.get_book_by_id') as mock_get_book, \
             patch('app.db.supabase.supabase_ops.add_book_to_library') as mock_add:
            
            mock_get_user.return_value = mock_user
            mock_get_book.return_value = mock_book
            mock_add.return_value = {
                "user_book_id": "ub-123",
                "book_id": mock_book["id"],
                "status": "want_to_read"
            }
            
            response = client.post(
                "/api/v1/books/library",
                headers=auth_headers,
                json={
                    "book_id": mock_book["id"],
                    "status": "want_to_read"
                }
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["book_id"] == mock_book["id"]
    
    def test_add_book_duplicate(self, client, auth_headers, mock_user, mock_book):
        """Test adding book already in library"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.add_book_to_library') as mock_add:
            
            mock_get_user.return_value = mock_user
            mock_add.side_effect = Exception("Book already in library")
            
            response = client.post(
                "/api/v1/books/library",
                headers=auth_headers,
                json={
                    "book_id": mock_book["id"],
                    "status": "want_to_read"
                }
            )
        
        assert response.status_code == status.HTTP_409_CONFLICT
    
    def test_add_book_invalid_status(self, client, auth_headers):
        """Test adding book with invalid status"""
        response = client.post(
            "/api/v1/books/library",
            headers=auth_headers,
            json={
                "book_id": "book-id",
                "status": "invalid_status"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_add_book_nonexistent(self, client, auth_headers, mock_user):
        """Test adding non-existent book"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.get_book_by_id') as mock_get_book:
            
            mock_get_user.return_value = mock_user
            mock_get_book.return_value = None
            
            response = client.post(
                "/api/v1/books/library",
                headers=auth_headers,
                json={
                    "book_id": "nonexistent-book-id",
                    "status": "want_to_read"
                }
            )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateLibraryBook:
    """Test updating books in library"""
    
    def test_update_book_status(self, client, auth_headers, mock_user, mock_book):
        """Test updating book reading status"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.update_user_book') as mock_update:
            
            mock_get_user.return_value = mock_user
            mock_update.return_value = {
                "user_book_id": "ub-123",
                "book_id": mock_book["id"],
                "status": "read"
            }
            
            response = client.patch(
                f"/api/v1/books/library/{mock_book['id']}",
                headers=auth_headers,
                json={"status": "read"}
            )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_book_progress(self, client, auth_headers, mock_user, mock_book):
        """Test updating reading progress"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.update_user_book') as mock_update:
            
            mock_get_user.return_value = mock_user
            mock_update.return_value = {
                "current_page": 100,
                "progress_percentage": 55.6
            }
            
            response = client.patch(
                f"/api/v1/books/library/{mock_book['id']}",
                headers=auth_headers,
                json={"current_page": 100}
            )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_book_rating(self, client, auth_headers, mock_user, mock_book):
        """Test updating book rating"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.update_user_book') as mock_update:
            
            mock_get_user.return_value = mock_user
            mock_update.return_value = {"rating": 5}
            
            response = client.patch(
                f"/api/v1/books/library/{mock_book['id']}",
                headers=auth_headers,
                json={"rating": 5, "review": "Excellent book!"}
            )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_book_invalid_rating(self, client, auth_headers):
        """Test updating with invalid rating"""
        response = client.patch(
            "/api/v1/books/library/book-id",
            headers=auth_headers,
            json={"rating": 6}  # Invalid (max is 5)
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRemoveBookFromLibrary:
    """Test removing books from library"""
    
    def test_remove_book_success(self, client, auth_headers, mock_user, mock_book):
        """Test successfully removing book"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.remove_book_from_library') as mock_remove:
            
            mock_get_user.return_value = mock_user
            mock_remove.return_value = True
            
            response = client.delete(
                f"/api/v1/books/library/{mock_book['id']}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_remove_book_not_in_library(self, client, auth_headers, mock_user):
        """Test removing book not in library"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.remove_book_from_library') as mock_remove:
            
            mock_get_user.return_value = mock_user
            mock_remove.return_value = False
            
            response = client.delete(
                "/api/v1/books/library/nonexistent-book",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestReadingStatistics:
    """Test reading statistics endpoints"""
    
    def test_get_reading_stats(self, client, auth_headers, mock_user):
        """Test getting user reading statistics"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get_user, \
             patch('app.db.supabase.supabase_ops.get_reading_statistics') as mock_get_stats:
            
            mock_get_user.return_value = mock_user
            mock_get_stats.return_value = {
                "total_books": 45,
                "books_read": 28,
                "books_reading": 5,
                "total_pages_read": 8540,
                "average_rating": 4.2
            }
            
            response = client.get("/api/v1/books/stats", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_books"] == 45
        assert data["books_read"] == 28