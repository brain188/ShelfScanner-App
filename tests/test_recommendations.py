"""
Tests for recommendation endpoints.
Tests personalized recommendations, similar books, and AI explanations.
"""
import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock


class TestPersonalizedRecommendations:
    """Test personalized recommendation endpoints"""
    
    def test_get_recommendations_success(self, client, auth_headers, mock_user, mock_recommendations):
        """Test getting personalized recommendations"""
        with patch('app.api.v1.recommendations.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
             patch('app.api.v1.recommendations.supabase_ops.get_user_books', new_callable=AsyncMock) as mock_get_book, \
             patch('app.api.v1.recommendations.recommendation_engine.get_recommendations', new_callable=AsyncMock) as mock_recs:
            
            mock_get_user.return_value = mock_user
            mock_get_book.return_value = {
                "books": [
                    {
                        "book_id": "book-1",
                        "title": "Test Book",
                        "authors": ["Author"],
                        "favorite": True,
                        "status": "read",
                        "rating": 5
                    }
                ],
                "total": 1
            }
            mock_recs.return_value = {
                "recommendations": mock_recommendations,
                "total": len(mock_recommendations),
                "algorithm": "hybrid"
            }
            
            response = client.get("/api/v1/recommendations", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
    
    def test_get_recommendations_empty_library(self, client, auth_headers, mock_user):
        """Test recommendations when user has empty library"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
             patch('app.services.recommendation_engine.get_personalized_recommendations', new_callable=AsyncMock) as mock_recs:
            
            mock_get_user.return_value = mock_user
            mock_recs.return_value = {
                "recommendations": [],
                "message": "Add books to your library to get recommendations"
            }
            
            response = client.get("/api/v1/recommendations", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_recommendations_with_algorithm(self, client, auth_headers, mock_user):
        """Test recommendations with specific algorithm"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
             patch('app.services.recommendation_engine.get_personalized_recommendations', new_callable=AsyncMock) as mock_recs:
            
            mock_get_user.return_value = mock_user
            mock_recs.return_value = {"recommendations": [], "algorithm": "content_based"}
            
            response = client.get(
                "/api/v1/recommendations?algorithm=content_based",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK


class TestSimilarBooks:
    """Test similar books recommendation"""
    
    def test_get_similar_books_success(self, client, auth_headers, mock_book, mock_books):
        """Test getting similar books"""
        with patch('app.db.supabase.supabase_ops.get_book_by_id', new_callable=AsyncMock) as mock_get_book, \
             patch('app.services.recommendation_engine.find_similar_books', new_callable=AsyncMock) as mock_similar:
            
            mock_get_book.return_value = mock_book
            mock_similar.return_value = {
                "similar_books": mock_books,
                "search_method": "vector_similarity"
            }
            
            response = client.get(
                f"/api/v1/recommendations/similar/{mock_book['id']}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "similar_books" in data
    
    def test_get_similar_books_not_found(self, client, auth_headers):
        """Test similar books for non-existent book"""
        with patch('app.db.supabase.supabase_ops.get_book_by_id', new_callable=AsyncMock) as mock_get_book:
            mock_get_book.return_value = None
            
            response = client.get(
                "/api/v1/recommendations/similar/nonexistent-id",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAIExplanations:
    """Test AI-powered recommendation explanations"""
    
    def test_get_ai_explanation_success(self, client, auth_headers, mock_book, mock_openai_response):
        """Test getting AI explanation for recommendation"""
        with patch('app.db.supabase.supabase_ops.get_book_by_id', new_callable=AsyncMock) as mock_get_book, \
             patch('app.services.recommendation_engine.generate_recommendation_explanation', new_callable=AsyncMock) as mock_ai:
            
            mock_get_book.return_value = mock_book
            mock_ai.return_value = {
                "explanation": "This book is recommended because..."
            }
            
            response = client.get(
                f"/api/v1/recommendations/explain/{mock_book['id']}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "explanation" in data
    
    def test_get_ai_explanation_rate_limit(self, client, auth_headers, mock_book):
        """Test AI explanation rate limiting"""
        # Make requests until rate limit
        for _ in range(4):  # Rate limit is 3/hour
            with patch('app.db.supabase.supabase_ops.get_book_by_id', new_callable=AsyncMock) as mock_get_book, \
                 patch('app.services.recommendation_engine.generate_recommendation_explanation', new_callable=AsyncMock) as mock_ai:
                
                mock_get_book.return_value = mock_book
                mock_ai.return_value = {"explanation": "..."}
                
                client.get(
                    f"/api/v1/recommendations/explain/{mock_book['id']}",
                    headers=auth_headers
                )
        
        # This request should be rate limited
        response = client.get(
            f"/api/v1/recommendations/explain/{mock_book['id']}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestRecommendationInteractions:
    """Test tracking user interactions with recommendations"""
    
    def test_track_recommendation_click(self, client, auth_headers, mock_user):
        """Test tracking when user clicks recommendation"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
             patch('app.db.supabase.supabase_ops.update_recommendation_interaction', new_callable=AsyncMock) as mock_update:
            
            mock_get_user.return_value = mock_user
            mock_update.return_value = True
            
            response = client.post(
                "/api/v1/recommendations/rec-id/track",
                headers=auth_headers,
                json={"action": "clicked"}
            )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_refresh_recommendations(self, client, auth_headers, mock_user):
        """Test refreshing cached recommendations"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
             patch('app.services.recommendation_engine.refresh_recommendations', new_callable=AsyncMock) as mock_refresh:
            
            mock_get_user.return_value = mock_user
            mock_refresh.return_value = {"message": "Recommendations refreshed"}
            
            response = client.post(
                "/api/v1/recommendations/refresh",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK