"""
Authentication API endpoints.
Handles user registration, login, token refresh, and password management.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import (
    token_manager,
    password_manager,
    get_current_user,
    get_current_active_user
)
from app.core.logging import get_logger
from app.models.user import (
    UserCreate,
    User,
    Token,
    LoginRequest,
    RefreshTokenRequest,
    PasswordChangeRequest,
    UserProfile
)
from app.db.supabase import supabase_ops

logger = get_logger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.rate_limit_per_hour}/hour")
async def register(request: Request, user_data: UserCreate) -> User:
    """
    Register a new user.
    
    Rate limited to prevent abuse.
    """
    try:
        # Check if user already exists
        existing_user = await supabase_ops.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = password_manager.hash_password(user_data.password)
        
        # Create user
        user_dict = {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "hashed_password": hashed_password,
            "role": "user",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        created_user = await supabase_ops.create_user(user_dict)
        
        logger.info("User registered", user_id=created_user["id"], email=user_data.email)
        
        return User(**created_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User registration failed", email=user_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def login(request: Request, login_data: LoginRequest) -> Token:
    """
    Login user and return access + refresh tokens.
    
    Rate limited to prevent brute force attacks.
    """
    try:
        # Get user by email
        user = await supabase_ops.get_user_by_email(login_data.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not password_manager.verify_password(
            login_data.password,
            user["hashed_password"]
        ):
            logger.warning("Failed login attempt", email=login_data.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Create tokens
        token_data = {
            "sub": user["id"],
            "email": user["email"],
            "role": user.get("role", "user")
        }
        
        access_token = token_manager.create_access_token(token_data)
        refresh_token = token_manager.create_refresh_token(token_data)
        
        # Update last login
        await supabase_ops.update_user(
            user["id"],
            {"last_login": datetime.now(timezone.utc).isoformat()}
        )
        
        logger.info("User logged in", user_id=user["id"], email=login_data.email)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", email=login_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest) -> Token:
    """
    Refresh access token using refresh token.
    """
    try:
        # Verify refresh token
        payload = token_manager.verify_token(
            refresh_data.refresh_token,
            token_type="refresh"
        )
        
        # Create new access token
        token_data = {
            "sub": payload["sub"],
            "email": payload["email"],
            "role": payload["role"]
        }
        
        access_token = token_manager.create_access_token(token_data)
        refresh_token = token_manager.create_refresh_token(token_data)
        
        logger.info("Token refreshed", user_id=payload["sub"])
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except Exception as e:
        logger.warning("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_active_user)
) -> UserProfile:
    """
    Get current user profile.
    """
    try:
        user = await supabase_ops.get_user_by_id(current_user["user_id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserProfile(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user profile", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )


@router.put("/me", response_model=UserProfile)
async def update_profile(
    updates: dict,
    current_user: dict = Depends(get_current_active_user)
) -> UserProfile:
    """
    Update current user profile.
    """
    try:
        # Update user
        updated_user = await supabase_ops.update_user(
            current_user["user_id"],
            {**updates, "updated_at": datetime.now(timezone.utc).isoformat()}
        )
        
        logger.info("User profile updated", user_id=current_user["user_id"])
        
        return UserProfile(**updated_user)
        
    except Exception as e:
        logger.error("Profile update failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Change user password.
    """
    try:
        # Get user
        user = await supabase_ops.get_user_by_id(current_user["user_id"])
        
        # Verify old password
        if not password_manager.verify_password(
            password_data.old_password,
            user["hashed_password"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        # Hash new password
        new_hashed = password_manager.hash_password(password_data.new_password)
        
        # Update password
        await supabase_ops.update_user(
            current_user["user_id"],
            {
                "hashed_password": new_hashed,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        logger.info("Password changed", user_id=current_user["user_id"])
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_active_user)):
    """
    Logout user (client should discard tokens).
    """
    logger.info("User logged out", user_id=current_user["user_id"])
    return {"message": "Logged out successfully"}