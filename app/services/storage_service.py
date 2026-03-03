"""
Storage service for handling file uploads to Supabase Storage.
"""
import uuid
from typing import Optional
from pathlib import Path

from fastapi import UploadFile, HTTPException, status

from app.core.config import settings
from app.core.logging import get_logger
from app.db.supabase import supabase_client

logger = get_logger(__name__)


class StorageService:
    """Service for managing file uploads to Supabase Storage"""
    
    def __init__(self):
        self.scan_bucket = "scans"
        self.profile_bucket = "profiles"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_image_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    
    async def upload_scan_image(
        self,
        file: UploadFile,
        user_id: str
    ) -> str:
        """
        Upload scan image/PDF to Supabase Storage.
        
        Args:
            file: The uploaded file
            user_id: User ID for organizing files
            
        Returns:
            Public URL of the uploaded file
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate file type
            if file.content_type not in self.allowed_image_types and file.content_type != "application/pdf":
                logger.warning(
                    "Invalid file type for scan",
                    content_type=file.content_type,
                    user_id=user_id
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not allowed: {file.content_type}"
                )
            
            # Read file content
            content = await file.read()
            file_size = len(content)
            
            # Validate file size
            if file_size > self.max_file_size:
                logger.warning(
                    "File too large for scan",
                    size=file_size,
                    max_size=self.max_file_size,
                    user_id=user_id
                )
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Max size: {self.max_file_size / 1024 / 1024}MB"
                )
            
            # Generate unique filename
            file_ext = Path(file.filename).suffix if file.filename else ".jpg"
            unique_filename = f"{user_id}/scans/{uuid.uuid4()}{file_ext}"
            
            # Upload to Supabase Storage
            response = supabase_client.storage.from_(self.scan_bucket).upload(
                unique_filename,
                content,
                file_options={"content-type": file.content_type}
            )
            
            # Get public URL
            public_url = supabase_client.storage.from_(self.scan_bucket).get_public_url(unique_filename)
            
            logger.info(
                "Scan image uploaded successfully",
                filename=unique_filename,
                size=file_size,
                user_id=user_id
            )
            
            return public_url
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to upload scan image",
                error=str(e),
                user_id=user_id,
                filename=file.filename if file.filename else "unknown"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file"
            )
    
    async def upload_profile_image(
        self,
        file: UploadFile,
        user_id: str
    ) -> str:
        """
        Upload profile image to Supabase Storage.
        
        Args:
            file: The uploaded image file
            user_id: User ID
            
        Returns:
            Public URL of the uploaded image
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate file type
            if file.content_type not in self.allowed_image_types:
                logger.warning(
                    "Invalid file type for profile image",
                    content_type=file.content_type,
                    user_id=user_id
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_image_types)}"
                )
            
            # Read file content
            content = await file.read()
            file_size = len(content)
            
            # Validate file size (5MB for profile images)
            max_profile_size = 5 * 1024 * 1024
            if file_size > max_profile_size:
                logger.warning(
                    "Profile image too large",
                    size=file_size,
                    max_size=max_profile_size,
                    user_id=user_id
                )
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Max size: {max_profile_size / 1024 / 1024}MB"
                )
            
            # Generate unique filename
            file_ext = Path(file.filename).suffix if file.filename else ".jpg"
            unique_filename = f"{user_id}/profile{file_ext}"
            
            # Delete old profile image if exists
            try:
                existing_files = supabase_client.storage.from_(self.profile_bucket).list(user_id)
                if existing_files:
                    for existing_file in existing_files:
                        if existing_file['name'].startswith('profile'):
                            supabase_client.storage.from_(self.profile_bucket).remove([f"{user_id}/{existing_file['name']}"])
                            logger.info("Old profile image deleted", user_id=user_id)
            except Exception as e:
                logger.warning("Failed to delete old profile image", error=str(e), user_id=user_id)
            
            # Upload to Supabase Storage
            response = supabase_client.storage.from_(self.profile_bucket).upload(
                unique_filename,
                content,
                file_options={
                    "content-type": file.content_type,
                    "upsert": "true"  # Overwrite if exists
                }
            )
            
            # Get public URL
            public_url = supabase_client.storage.from_(self.profile_bucket).get_public_url(unique_filename)
            
            logger.info(
                "Profile image uploaded successfully",
                filename=unique_filename,
                size=file_size,
                user_id=user_id
            )
            
            return public_url
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to upload profile image",
                error=str(e),
                user_id=user_id,
                filename=file.filename if file.filename else "unknown"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload profile image"
            )
    
    async def delete_file(
        self,
        file_path: str,
        bucket: str = "scans"
    ) -> bool:
        """
        Delete a file from Supabase Storage.
        
        Args:
            file_path: Path to the file in storage
            bucket: Storage bucket name
            
        Returns:
            True if deleted successfully
        """
        try:
            supabase_client.storage.from_(bucket).remove([file_path])
            logger.info("File deleted successfully", file_path=file_path, bucket=bucket)
            return True
        except Exception as e:
            logger.error("Failed to delete file", error=str(e), file_path=file_path, bucket=bucket)
            return False


# Create singleton instance
storage_service = StorageService()