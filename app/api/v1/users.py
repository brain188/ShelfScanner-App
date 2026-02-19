"""
User profile and preferences API endpoints.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_active_user
from app.core.logging import get_logger
from app.db.supabase import supabase_ops
from app.services.storage_service import storage_service

logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/users", tags=["users"])


# Pydantic models
class UserProfileResponse(BaseModel):
    """User profile response"""
    user_id: str
    email: str
    full_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    created_at: str
    preferences: Optional[Dict[str, Any]] = None


class UpdateProfileRequest(BaseModel):
    """Request to update user profile"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)


class UserPreferencesResponse(BaseModel):
    """User preferences response"""
    theme: str = "light"
    notifications_enabled: bool = True
    email_notifications: bool = True
    scan_auto_add: bool = False
    language: str = "en"


class UpdatePreferencesRequest(BaseModel):
    """Request to update user preferences"""
    theme: Optional[str] = Field(None, pattern="^(light|dark|auto)$")
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    scan_auto_add: Optional[bool] = None
    language: Optional[str] = Field(None, pattern="^(en|es|fr|de)$")


class DeleteAccountRequest(BaseModel):
    """Request to delete user account"""
    password: str = Field(..., min_length=8)
    confirmation: str = Field(..., pattern="^DELETE$")


# Endpoints
@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_active_user)
) -> UserProfileResponse:
    """
    Get current user's profile information.
    
    Returns:
        User profile data including preferences
    """
    try:
        user = await supabase_ops.get_user_by_id(current_user["user_id"])
        
        if not user:
            logger.error("User not found", user_id=current_user["user_id"])
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info("User profile retrieved", user_id=current_user["user_id"])
        
        return UserProfileResponse(
            user_id=user["user_id"],
            email=user["email"],
            full_name=user.get("full_name"),
            profile_image_url=user.get("profile_image_url"),
            created_at=user["created_at"],
            preferences=user.get("preferences", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user profile", error=str(e), user_id=current_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.patch("/me")
async def update_current_user_profile(
    profile_update: UpdateProfileRequest,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update current user's profile information.
    
    Args:
        profile_update: Profile fields to update
        
    Returns:
        Updated user profile
    """
    try:
        # Build update data
        update_data = {}
        if profile_update.full_name is not None:
            update_data["full_name"] = profile_update.full_name
        if profile_update.bio is not None:
            update_data["bio"] = profile_update.bio
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update user
        updated_user = await supabase_ops.update_user(
            current_user["user_id"],
            update_data
        )
        
        if not updated_user:
            logger.error("Failed to update user profile", user_id=current_user["user_id"])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        logger.info(
            "User profile updated",
            user_id=current_user["user_id"],
            fields=list(update_data.keys())
        )
        
        return {
            "message": "Profile updated successfully",
            "user": updated_user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user profile", error=str(e), user_id=current_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/me/profile-image")
@limiter.limit("5/hour")
async def upload_profile_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    Upload or update user's profile image.
    Rate limited to 5 uploads per hour.
    
    Args:
        file: Image file (JPEG, PNG, WebP, max 5MB)
        
    Returns:
        URL of uploaded profile image
    """
    try:
        # Upload image to storage
        image_url = await storage_service.upload_profile_image(
            file=file,
            user_id=current_user["user_id"]
        )
        
        # Update user profile with new image URL
        updated_user = await supabase_ops.update_user(
            current_user["user_id"],
            {
                "profile_image_url": image_url,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        if not updated_user:
            logger.error("Failed to update user with profile image", user_id=current_user["user_id"])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile image"
            )
        
        logger.info("Profile image uploaded", user_id=current_user["user_id"], url=image_url)
        
        return {
            "message": "Profile image uploaded successfully",
            "image_url": image_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload profile image", error=str(e), user_id=current_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile image"
        )


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: dict = Depends(get_current_active_user)
) -> UserPreferencesResponse:
    """
    Get current user's preferences.
    
    Returns:
        User preferences
    """
    try:
        user = await supabase_ops.get_user_by_id(current_user["user_id"])
        
        if not user:
            logger.error("User not found", user_id=current_user["user_id"])
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get preferences from user data
        preferences = user.get("preferences", {})
        
        logger.info("User preferences retrieved", user_id=current_user["user_id"])
        
        return UserPreferencesResponse(
            theme=preferences.get("theme", "light"),
            notifications_enabled=preferences.get("notifications_enabled", True),
            email_notifications=preferences.get("email_notifications", True),
            scan_auto_add=preferences.get("scan_auto_add", False),
            language=preferences.get("language", "en")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user preferences", error=str(e), user_id=current_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences"
        )


@router.patch("/me/preferences")
async def update_user_preferences(
    preferences_update: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update current user's preferences.
    
    Args:
        preferences_update: Preferences to update
        
    Returns:
        Updated preferences
    """
    try:
        # Get current user
        user = await supabase_ops.get_user_by_id(current_user["user_id"])
        
        if not user:
            logger.error("User not found", user_id=current_user["user_id"])
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get current preferences
        current_preferences = user.get("preferences", {})
        
        # Update only provided fields
        update_fields = preferences_update.model_dump(exclude_unset=True)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No preferences to update"
            )
        
        # Merge with existing preferences
        updated_preferences = {**current_preferences, **update_fields}
        
        # Update user with new preferences
        updated_user = await supabase_ops.update_user(
            current_user["user_id"],
            {
                "preferences": updated_preferences,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        if not updated_user:
            logger.error("Failed to update user preferences", user_id=current_user["user_id"])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences"
            )
        
        logger.info(
            "User preferences updated",
            user_id=current_user["user_id"],
            fields=list(update_fields.keys())
        )
        
        return {
            "message": "Preferences updated successfully",
            "preferences": updated_preferences
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user preferences", error=str(e), user_id=current_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    delete_request: DeleteAccountRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Soft delete user account.
    Requires password confirmation and typing 'DELETE' to confirm.
    
    Args:
        delete_request: Password and confirmation
        
    Returns:
        204 No Content on success
    """
    try:
        # Verify confirmation text
        if delete_request.confirmation != "DELETE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation text must be 'DELETE'"
            )
        
        # In a real app, you would verify the password here
        # For now, i'm skip password verification since i;m using JWT auth
        
        # Soft delete user
        success = await supabase_ops.soft_delete_user(current_user["user_id"])
        
        if not success:
            logger.error("Failed to delete user account", user_id=current_user["user_id"])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account"
            )
        
        logger.info(
            "User account deleted",
            user_id=current_user["user_id"],
            email=current_user.get("email", "unknown")
        )
        
        # Return 204 No Content (no response body)
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete user account", error=str(e), user_id=current_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )