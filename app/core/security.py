"""
Security module for authentication, authorization, and JWT handling.
Implements secure password hashing and token generation/validation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger
from app.db.supabase import supabase_ops

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


class SecurityError(Exception):
    """Base security exception"""
    pass


class TokenManager:
    """
    Token management class for JWT creation and validation.
    Implements secure token generation with configurable expiration.
    """
    
    def __init__(self):
        """Initialize token manager"""
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Payload data to encode in token
            expires_delta: Optional custom expiration time
        
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        logger.debug(
            "Access token created",
            user_id=data.get("sub"),
            expires_at=expire.isoformat()
        )
        
        return encoded_jwt
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token.
        
        Args:
            data: Payload data to encode in token
            expires_delta: Optional custom expiration time
        
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.refresh_token_expire_days
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        logger.debug(
            "Refresh token created",
            user_id=data.get("sub"),
            expires_at=expire.isoformat()
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type (access or refresh)
        
        Returns:
            Decoded token payload
        
        Raises:
            SecurityError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise SecurityError(f"Invalid token type. Expected {token_type}")
            
            logger.debug(
                "Token verified",
                user_id=payload.get("sub"),
                token_type=token_type
            )
            
            return payload
            
        except JWTError as e:
            logger.warning("Token verification failed", error=str(e))
            raise SecurityError(f"Invalid token: {str(e)}")


class PasswordManager:
    """
    Password management class for secure hashing and verification.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
        
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit"
        
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in password):
            return False, "Password must contain at least one special character"
        
        return True, None


# Global instances
token_manager = TokenManager()
password_manager = PasswordManager()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials
    
    Returns:
        User data from token payload
    
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = token_manager.verify_token(token, token_type="access")
        user_id: str = payload.get("sub")
        
        if user_id is None:
            logger.warning("Token missing user ID")
            raise credentials_exception
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "user")
        }
        
    except SecurityError as e:
        logger.warning("Authentication failed", error=str(e))
        raise credentials_exception


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to get current active user.
    Can be extended to check user status in database.
    
    Args:
        current_user: Current user from token
    
    Returns:
        Active user data with database verification status
    
    Raises:
        HTTPException: If user is not active ot not found
    """

    try:
        # get user from database to verify active status
        user = await supabase_ops.get_user_by_id(current_user["user_id"])

        if not user:
            logger.warning("User not found in database", user_id=current_user["user_id"])
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # check if user account is active
        if not user.get("is_active", False):
            logger.warning(
                "Inactive user attempted access", 
                user_id=current_user["user_id"],
                email=user.get("email"),
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive, Please contact support.",
            )
        
        # Check if user is deleted(soft delete)
        if user.get("deleted_at") is not None:
            logger.warning(
                "Deleted user attempted access", 
                user_id=current_user["user_id"],
                email=user.get("email"),
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account has been deleted.",
            )
        
        # Update last login timestamp(done async to avoid delaying response or blocking)
        try:
            await supabase_ops.update_user_last_login(current_user["user_id"])
        except Exception as e:
            # don't block user access if last login update fails
            logger.error(
                "Failed to update user last login",
                user_id=current_user["user_id"],
                error=str(e)
            )

        # Merge database user data with token data
        return{
            "user_id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": user.get("role", "user"),
            "is_active": user.get("is_active"),
            "is_email_verified": user.get("is_email_verified", False),
            "profile_image_url": user.get("profile_image_url"),
            "created_at": user.get("created_at"),
        }
    
    except HTTPException:
        # re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error("Error checking user active status", user_id=current_user["user_id"], error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying user status",
        )


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.
    
    Args:
        required_role: Required role for access
    
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("role", "user")
        
        if user_role != required_role and user_role != "admin":
            logger.warning(
                "Access denied - insufficient permissions",
                user_id=current_user.get("user_id"),
                required_role=required_role,
                user_role=user_role
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker


__all__ = [
    "token_manager",
    "password_manager",
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "SecurityError"
]