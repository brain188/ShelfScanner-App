"""
Tests for authentication endpoints.
Tests registration, login, token refresh, and user management.
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock

from app.core.security import token_manager, password_manager

# Skip tests for features not yet implemented
pytestmark_password_reset = pytest.mark.skip(reason="Password reset endpoints not implemented")
pytestmark_email_verification = pytest.mark.skip(reason="Email verification not implemented")

class TestUserRegistration:
    """Test user registration endpoint"""
    
    def test_register_user_success(self, client, user_data, mock_user, mock_ops):
        """Test successful user registration"""

        with patch('app.api.v1.auth.supabase_ops.get_user_by_email', new_callable=AsyncMock) as mock_get_email, \
             patch('app.api.v1.auth.supabase_ops.create_user', new_callable=AsyncMock) as mock_create:
            
            mock_get_email.return_value = None  # No existing user
            
            mock_create.return_value = {
                "id": "user-id",
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "role": "user",
                "is_active": True,
                "is_email_verified": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            response = client.post("/api/v1/auth/register", json=user_data)
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["email"] == user_data["email"]
            assert data["full_name"] == user_data["full_name"]
            assert data["role"] == "user"
            assert "password" not in data
            assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client, user_data):
        """Test registration with duplicate email fails"""
        # Register first time
        client.post("/api/v1/auth/register", json=user_data)
        
        # Try to register again with same email
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()
    
    @pytest.mark.parametrize("invalid_email", [
        "invalid-email",
        "@example.com",
        "user@",
        "user @example.com",
        ""
    ])
    def test_register_invalid_email(self, client, user_data, invalid_email):
        """Test registration with invalid email formats"""
        user_data["email"] = invalid_email
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.parametrize("weak_password", [
        "short",
        "nouppercase123!",
        "NOLOWERCASE123!",
        "NoDigits!@#",
        "NoSpecial123"
    ])
    def test_register_weak_password(self, client, user_data, weak_password):
        """Test registration with weak passwords"""
        user_data["password"] = weak_password
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_missing_required_fields(self, client):
        """Test registration with missing required fields"""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com"
            # Missing password
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_password_hashing(self, client, user_data):
        """Test that password is properly hashed"""
        with patch('app.db.supabase.supabase_ops.get_user_by_email', new_callable=AsyncMock) as mock_get, \
             patch('app.db.supabase.supabase_ops.create_user', new_callable=AsyncMock) as mock_create:
            
            mock_get.return_value = None  # No existing user
            mock_create.return_value = {
                "id": "user-id",
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "role": "user",
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            
            # Verify create_user was called with hashed password
            call_args = mock_create.call_args[0][0]
            assert call_args["hashed_password"] != user_data["password"]
            assert call_args["hashed_password"].startswith("$2b$")


class TestUserLogin:
    """Test user login endpoint"""
    
    def test_login_success(self, client, user_data, mock_user):
        """Test successful login"""
        # First register
        with patch('app.db.supabase.supabase_ops.create_user', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_user
            client.post("/api/v1/auth/register", json=user_data)
        
        # Then login
        with patch('app.db.supabase.supabase_ops.get_user_by_email', new_callable=AsyncMock) as mock_get, \
             patch('app.db.supabase.supabase_ops.update_user', new_callable=AsyncMock):
            mock_get.return_value = {
                **mock_user,
                "hashed_password": password_manager.hash_password(user_data["password"])
            }
            
            response = client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_wrong_password(self, client, user_data, mock_user):
        """Test login with wrong password"""
        with patch('app.db.supabase.supabase_ops.get_user_by_email', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                **mock_user,
                "hashed_password": password_manager.hash_password(user_data["password"])
            }
            
            response = client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": "WrongPassword123!"
            })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "credentials" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        with patch('app.db.supabase.supabase_ops.get_user_by_email', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            response = client.post("/api/v1/auth/login", json={
                "email": "nonexistent@example.com",
                "password": "Password123!"
            })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_inactive_user(self, client, inactive_user):
        """Test login with inactive user account"""
        with patch('app.db.supabase.supabase_ops.get_user_by_email', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                **inactive_user,
                "hashed_password": password_manager.hash_password("Password123!")
            }
            
            response = client.post("/api/v1/auth/login", json={
                "email": inactive_user["email"],
                "password": "Password123!"
            })
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["detail"].lower()
    
    def test_login_deleted_user(self, client, deleted_user):
        """Test login with soft-deleted user"""
        with patch('app.db.supabase.supabase_ops.get_user_by_email', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                **deleted_user,
                "hashed_password": password_manager.hash_password("Password123!")
            }
            
            response = client.post("/api/v1/auth/login", json={
                "email": deleted_user["email"],
                "password": "Password123!"
            })
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTokenRefresh:
    """Test token refresh endpoint"""
    
    def test_refresh_token_success(self, client, mock_user):
        """Test successful token refresh"""
        # Create refresh token
        refresh_token_data = {
            "sub": mock_user["id"],
            "email": mock_user["email"],
            "role": mock_user["role"],
            "type": "refresh"
        }
        refresh_token = token_manager.create_access_token(
            refresh_token_data,
            expires_delta=timedelta(days=7)
        )
        
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token"""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-token"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_expired(self, client, expired_token):
        """Test refresh with expired token"""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": expired_token
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_with_access_token_fails(self, client, auth_token):
        """Test that access token cannot be used for refresh"""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": auth_token
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUser:
    """Test get current user endpoint"""
    
    def test_get_current_user_success(self, client, auth_headers, mock_user):
        """Test getting current user with valid token"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_user
            
            response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == mock_user["email"]
        assert data["role"] == mock_user["role"]
        assert "hashed_password" not in data
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_expired_token(self, client, expired_token):
        """Test getting current user with expired token"""
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPasswordChange:
    """Test password change functionality"""
    
    def test_change_password_success(self, client, auth_headers, mock_user):
        """Test successful password change"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get, \
             patch('app.db.supabase.supabase_ops.update_user', new_callable=AsyncMock) as mock_update:
            
            mock_get.return_value = {
                **mock_user,
                "hashed_password": password_manager.hash_password("OldPassword123!")
            }
            mock_update.return_value = mock_user
            
            response = client.post("/api/v1/auth/change-password", headers=auth_headers, json={
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!"
            })
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_change_password_wrong_old_password(self, client, auth_headers, mock_user):
        """Test password change with wrong old password"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                **mock_user,
                "hashed_password": password_manager.hash_password("OldPassword123!")
            }
            
            response = client.post("/api/v1/auth/change-password", headers=auth_headers, json={
                "old_password": "WrongPassword123!",
                "new_password": "NewPassword123!"
            })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_weak_new_password(self, client, auth_headers):
        """Test password change with weak new password"""

        with patch('app.core.security.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_security, \
            patch('app.api.v1.auth.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_auth:
            
            user_data = {
                "id": "user-id",
                "email": "test@example.com",
                "role": "user",
                "hashed_password": password_manager.hash_password("OldPassword123!"),
                "is_active": True,
                "deleted_at": None
            }

            mock_security.return_value = user_data
            mock_auth.return_value = user_data
            
            response = client.post("/api/v1/auth/change-password", headers=auth_headers, json={
                "old_password": "OldPassword123!",
                "new_password": "weak"
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.skip(reason="Password reset not implemented")
class TestPasswordReset:
    """Test password reset functionality"""
    
    def test_request_password_reset(self, client, user_data):
        """Test requesting password reset"""
        response = client.post("/api/v1/auth/request-password-reset", json={
            "email": user_data["email"]
        })
        
        # Should return 200 even if email doesn't exist (security)
        assert response.status_code == status.HTTP_200_OK
    
    def test_reset_password_with_token(self, client):
        """Test resetting password with valid token"""
        reset_token = "valid-reset-token"
        
        with patch('app.db.supabase.supabase_ops.get_user_by_reset_token', new_callable=AsyncMock) as mock_get, \
             patch('app.db.supabase.supabase_ops.update_user', new_callable=AsyncMock) as mock_update:
            
            mock_get.return_value = {
                "id": "user-id",
                "email": "user@example.com",
                "password_reset_token": reset_token,
                "password_reset_expires": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            }
            mock_update.return_value = {}
            
            response = client.post("/api/v1/auth/reset-password", json={
                "token": reset_token,
                "new_password": "NewPassword123!"
            })
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_reset_password_expired_token(self, client):
        """Test resetting password with expired token"""
        reset_token = "expired-reset-token"
        
        with patch('app.db.supabase.supabase_ops.get_user_by_reset_token', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "id": "user-id",
                "password_reset_token": reset_token,
                "password_reset_expires": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            }
            
            response = client.post("/api/v1/auth/reset-password", json={
                "token": reset_token,
                "new_password": "NewPassword123!"
            })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.skip(reason="Email verification not implemented")
class TestEmailVerification:
    """Test email verification functionality"""
    
    def test_send_verification_email(self, client, auth_headers, mock_user):
        """Test sending verification email"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get, \
             patch('app.services.email_service.send_verification_email', new_callable=AsyncMock) as mock_email:
            
            mock_get.return_value = {**mock_user, "is_email_verified": False}
            mock_email.return_value = True
            
            response = client.post("/api/v1/auth/send-verification-email", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_verify_email_success(self, client):
        """Test email verification with valid token"""
        verification_token = "valid-verification-token"
        
        with patch('app.db.supabase.supabase_ops.verify_email_token', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = True
            
            response = client.post("/api/v1/auth/verify-email", json={
                "token": verification_token
            })
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_verify_email_invalid_token(self, client):
        """Test email verification with invalid token"""
        with patch('app.db.supabase.supabase_ops.verify_email_token', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = False
            
            response = client.post("/api/v1/auth/verify-email", json={
                "token": "invalid-token"
            })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAuthenticationFlow:
    """Integration tests for complete authentication flow"""
    
    def test_complete_auth_flow(self, client, user_data):
        """Test complete flow: register → login → access protected endpoint"""
        # 1. Register
        with patch('app.api.v1.auth.supabase_ops.get_user_by_email', new_callable=AsyncMock) as mock_get_email, \
             patch('app.api.v1.auth.supabase_ops.create_user', new_callable=AsyncMock) as mock_create:
            
            mock_get_email.return_value = None  # No existing user
            mock_create.return_value = {
                "id": "new-user-id",
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "role": "user",
                "is_active": True,
                "is_email_verified": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            register_response = client.post("/api/v1/auth/register", json=user_data)
            assert register_response.status_code == status.HTTP_201_CREATED
        
        # 2. Login
        with patch('app.api.v1.auth.supabase_ops.get_user_by_email', new_callable=AsyncMock) as mock_get_email, \
             patch('app.api.v1.auth.supabase_ops.update_user', new_callable=AsyncMock) as mock_update:
            
            mock_get_email.return_value = {
                "id": "new-user-id",
                "email": user_data["email"],
                "hashed_password": password_manager.hash_password(user_data["password"]),
                "is_active": True,
                "deleted_at": None,
            }

            mock_update.return_value = {}
            
            login_response = client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            assert login_response.status_code == status.HTTP_200_OK
            access_token = login_response.json()["access_token"]
        
        # 3. Access protected endpoint
        with patch('app.core.security.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_security, \
             patch('app.api.v1.auth.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_auth, \
             patch('app.core.security.supabase_ops.update_user_last_login', new_callable=AsyncMock):
            
            user_response = {
                "id": "new-user-id",
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "role": "user",
                "is_active": True,
                "deleted_at": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            mock_security.return_value = user_response
            mock_auth.return_value = user_response
            
            headers = {"Authorization": f"Bearer {access_token}"}
            protected_response = client.get("/api/v1/auth/me", headers=headers)
            assert protected_response.status_code == status.HTTP_200_OK
            assert protected_response.json()["email"] == user_data["email"]