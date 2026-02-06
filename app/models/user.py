"""
User data models and schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User full name")
    
    class ConfigDict:
        from_attributes = True


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8, description="User password")
    
    @field_validator("password")
    def validate_password(cls, v):
        """Validate password strength"""
        from app.core.security import password_manager
        is_valid, error_msg = password_manager.validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    
    @field_validator("password")
    def validate_password(cls, v):
        """Validate password strength if provided"""
        if v is not None:
            from app.core.security import password_manager
            is_valid, error_msg = password_manager.validate_password_strength(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v


class User(UserBase):
    """User model with all fields"""
    id: str = Field(..., description="User ID")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    is_active: bool = Field(default=True, description="Whether user is active")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class ConfigDict:
        from_attributes = True


class UserInDB(User):
    """User model as stored in database"""
    hashed_password: str = Field(..., description="Hashed password")


class UserProfile(BaseModel):
    """Public user profile"""
    id: str
    email: EmailStr
    full_name: Optional[str]
    role: UserRole
    created_at: datetime
    
    class ConfigDict:
        from_attributes = True


class Token(BaseModel):
    """Authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenPayload(BaseModel):
    """Token payload data"""
    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    role: UserRole = Field(..., description="User role")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    type: str = Field(..., description="Token type (access/refresh)")


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str = Field(..., description="Refresh token")


class PasswordChangeRequest(BaseModel):
    """Password change request model"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator("new_password")
    def validate_password(cls, v):
        """Validate new password strength"""
        from app.core.security import password_manager
        is_valid, error_msg = password_manager.validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr = Field(..., description="User email")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator("new_password")
    def validate_password(cls, v):
        """Validate new password strength"""
        from app.core.security import password_manager
        is_valid, error_msg = password_manager.validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    



# future update: try implementing dependency injection for password validation to avoid circular imports and improve testability.    