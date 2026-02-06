"""
Tests for user profile and preferences endpoints.
"""
import pytest
from fastapi import status
from unittest.mock import patch


class TestUserProfile:
    """Test user profile management"""
    
    def test_get_profile_success(self, client, auth_headers, mock_user):
        """Test getting user profile"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get:
            mock_get.return_value = mock_user
            
            response = client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == mock_user["email"]
    
    def test_update_profile_success(self, client, auth_headers, mock_user):
        """Test updating user profile"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get, \
             patch('app.db.supabase.supabase_ops.update_user') as mock_update:
            
            mock_get.return_value = mock_user
            mock_update.return_value = {**mock_user, "full_name": "New Name"}
            
            response = client.patch(
                "/api/v1/users/me",
                headers=auth_headers,
                json={"full_name": "New Name"}
            )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_profile_image(self, client, auth_headers, mock_user, test_image_path):
        """Test uploading profile image"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get, \
             patch('app.services.storage_service.upload_profile_image') as mock_upload:
            
            mock_get.return_value = mock_user
            mock_upload.return_value = "https://storage/profile.jpg"
            
            with open(test_image_path, "rb") as f:
                response = client.post(
                    "/api/v1/users/me/profile-image",
                    headers=auth_headers,
                    files={"file": ("profile.jpg", f, "image/jpeg")}
                )
        
        assert response.status_code == status.HTTP_200_OK


class TestUserPreferences:
    """Test user preferences management"""
    
    def test_get_preferences(self, client, auth_headers, mock_user):
        """Test getting user preferences"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get:
            mock_get.return_value = mock_user
            
            response = client.get("/api/v1/users/me/preferences", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_preferences(self, client, auth_headers, mock_user):
        """Test updating user preferences"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get, \
             patch('app.db.supabase.supabase_ops.update_user') as mock_update:
            
            mock_get.return_value = mock_user
            mock_update.return_value = mock_user
            
            response = client.patch(
                "/api/v1/users/me/preferences",
                headers=auth_headers,
                json={"theme": "dark", "notifications_enabled": False}
            )
        
        assert response.status_code == status.HTTP_200_OK


class TestUserDeletion:
    """Test user account deletion"""
    
    def test_delete_account_success(self, client, auth_headers, mock_user):
        """Test soft delete user account"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get, \
             patch('app.db.supabase.supabase_ops.soft_delete_user') as mock_delete:
            
            mock_get.return_value = mock_user
            mock_delete.return_value = True
            
            response = client.delete(
                "/api/v1/users/me",
                headers=auth_headers,
                json={"password": "TestPass123!"}
            )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT