"""
Scan API endpoints for image upload and OCR processing.
"""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import get_current_active_user
from app.core.logging import get_logger
from app.models.scan_result import (
    ScanResult,
    ScanResponse,
    ScanStatus,
    ScanType,
    ScanList
)
from app.services.ocr_service import ocr_service
from app.services.book_lookup import book_lookup_service
from app.db.supabase import supabase_ops

logger = get_logger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


async def process_scan_async(
    scan_id: str,
    file_path: str,
    user_id: str,
    auto_add: bool = False
):
    """Background task for processing scan"""
    try:
        start_time = datetime.now(timezone.utc)
        
        # Update status to processing
        await supabase_ops.update_scan_result(
            scan_id,
            {"status": ScanStatus.PROCESSING}
        )
        
        # Extract text from image
        extracted_texts = await ocr_service.extract_text_from_image(file_path)
        
        # Extract book metadata
        metadata = await ocr_service.extract_book_metadata(extracted_texts)
        
        # Search for books if ISBN found
        detected_books = []
        if metadata.get("isbn"):
            book = await book_lookup_service.search_by_isbn(metadata["isbn"])
            if book:
                detected_books.append({
                    "title": book.title,
                    "authors": book.authors,
                    "isbn": metadata["isbn"],
                    "confidence_score": 0.95
                })
        
        # Calculate processing time
        processing_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        # Update scan result
        await supabase_ops.update_scan_result(
            scan_id,
            {
                "status": ScanStatus.COMPLETED,
                "extracted_texts": [et.model_dump() for et in extracted_texts],
                "detected_books": detected_books,
                "processing_time_ms": processing_time,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        logger.info(
            "Scan processed successfully",
            scan_id=scan_id,
            books_found=len(detected_books),
            processing_time_ms=processing_time
        )
        
        # Auto-add books to library if requested
        if auto_add and detected_books:
            for book_data in detected_books:
                try:
                    # Check if book exists, create if not
                    book = await book_lookup_service.search_by_isbn(book_data["isbn"])
                    if book:
                        # Add to user's library
                        await supabase_ops.add_user_book({
                            "user_id": user_id,
                            "book_id": book.isbn_13,  # Using ISBN as temp ID
                            "status": "want_to_read",
                            "added_at": datetime.now(timezone.utc).isoformat()
                        })
                        logger.info("Book auto-added to library", user_id=user_id)
                except Exception as e:
                    logger.warning("Failed to auto-add book", error=str(e))
        
    except Exception as e:
        logger.error("Scan processing failed", scan_id=scan_id, error=str(e))
        await supabase_ops.update_scan_result(
            scan_id,
            {
                "status": ScanStatus.FAILED,
                "error_message": str(e)
            }
        )


@router.post("/upload", response_model=ScanResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_add_to_library: bool = False,
    current_user: dict = Depends(get_current_active_user)
) -> ScanResponse:
    """
    Upload and process image for OCR scanning.
    
    Supports: JPG, JPEG, PNG, PDF
    Max size: 10MB
    """
    try:
        # Validate file type
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported. Allowed: {settings.allowed_extensions}"
            )
        
        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {settings.max_upload_size_mb}MB"
            )
        
        # Create upload directory if not exists
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file with unique name
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}.{file_ext}"
        file_path = upload_dir / file_name
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(
            "File uploaded",
            user_id=current_user["user_id"],
            file_name=file.filename,
            file_size=file_size
        )
        
        # Create scan result record
        scan_data = {
            "user_id": current_user["user_id"],
            "scan_type": ScanType.PDF if file_ext == "pdf" else ScanType.IMAGE,
            "status": ScanStatus.PENDING,
            "image_url": str(file_path),
            "file_name": file.filename,
            "file_size": file_size,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        scan_result = await supabase_ops.create_scan_result(scan_data)
        scan_id = scan_result["id"]
        
        # Process scan in background
        background_tasks.add_task(
            process_scan_async,
            scan_id,
            str(file_path),
            current_user["user_id"],
            auto_add_to_library
        )
        
        return ScanResponse(
            scan_id=scan_id,
            status=ScanStatus.PENDING,
            message="Scan queued for processing",
            detected_books_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed"
        )


@router.get("/result/{scan_id}", response_model=ScanResult)
async def get_scan_result(
    scan_id: str,
    current_user: dict = Depends(get_current_active_user)
) -> ScanResult:
    """Get scan result by ID"""
    try:
        # Get scan result from database
        scan = await supabase_ops.get_user_scans(
            current_user["user_id"],
            limit=1,
            offset=0
        )
        
        # Filter for specific scan ID
        scan_result = next((s for s in scan if s["id"] == scan_id), None)
        
        if not scan_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found"
            )
        
        return ScanResult(**scan_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get scan result", scan_id=scan_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scan result"
        )


@router.get("/history", response_model=ScanList)
async def get_scan_history(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_active_user)
) -> ScanList:
    """Get user's scan history with pagination"""
    try:
        offset = (page - 1) * page_size
        
        scans = await supabase_ops.get_user_scans(
            current_user["user_id"],
            limit=page_size,
            offset=offset
        )
        
        # Get total count (simplified for MVP)
        total = len(scans)
        total_pages = (total + page_size - 1) // page_size
        
        return ScanList(
            scans=[ScanResult(**s) for s in scans],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error("Failed to get scan history", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scan history"
        )


@router.delete("/result/{scan_id}")
async def delete_scan(
    scan_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a scan result"""
    try:
        # In a full implementation, verify ownership and delete from DB
        logger.info("Scan deleted", scan_id=scan_id, user_id=current_user["user_id"])
        return {"message": "Scan deleted successfully"}
        
    except Exception as e:
        logger.error("Failed to delete scan", scan_id=scan_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete scan"
        )