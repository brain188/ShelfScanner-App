"""
Tests for security utilities and authentication mechanisms.
"""
import pytest
from datetime import timedelta
from app.core.security import (
    password_manager,
    token_manager
)


class TestPasswordManager:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "SecurePass123!"
        hashed = password_manager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "SecurePass123!"
        hashed = password_manager.hash_password(password)
        
        assert password_manager.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "SecurePass123!"
        hashed = password_manager.hash_password(password)
        
        assert password_manager.verify_password("WrongPass123!", hashed) is False
    
    @pytest.mark.parametrize("password,expected", [
        ("ValidPass123!", True),
        ("short", False),
        ("nouppercase123!", False),
        ("NOLOWERCASE123!", False),
        ("NoDigits!", False),
        ("NoSpecial123", False),
    ])
    def test_validate_password_strength(self, password, expected):
        """Test password strength validation"""
        is_valid, _ = password_manager.validate_password_strength(password)
        assert is_valid == expected


class TestTokenManager:
    """Test JWT token creation and verification"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "user123", "email": "user@example.com"}
        token = token_manager.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_access_token(self):
        """Test access token verification"""
        data = {"sub": "user123", "email": "user@example.com"}
        token = token_manager.create_access_token(data)
        
        payload = token_manager.verify_token(token, "access")
        
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"
    
    def test_token_expiration(self):
        """Test token expiration"""
        from app.core.security import SecurityError
        
        data = {"sub": "user123"}
        token = token_manager.create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(SecurityError):
            token_manager.verify_token(token, "access")