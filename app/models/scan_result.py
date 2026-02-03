"""
Scan result data models and schemas.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class ScanStatus(str, Enum):
    """Scan processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OCRConfidence(str, Enum):
    """OCR confidence level"""
    HIGH = "high"  # > 90%
    MEDIUM = "medium"  # 70-90%
    LOW = "low"  # < 70%


class ScanType(str, Enum):
    """Type of scan"""
    IMAGE = "image"
    PDF = "pdf"
    SINGLE_BOOK = "single_book"
    BOOKSHELF = "bookshelf"
    BATCH = "batch"


class ExtractedText(BaseModel):
    """Extracted text from OCR"""
    text: str = Field(..., description="Extracted text content")
    confidence: float = Field(..., ge=0, le=100, description="OCR confidence score")
    confidence_level: OCRConfidence = Field(..., description="Confidence level category")
    bounding_box: Optional[Dict[str, int]] = Field(None, description="Text bounding box coordinates")
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is high"""
        return self.confidence_level == OCRConfidence.HIGH


class DetectedBook(BaseModel):
    """Book detected from scan"""
    title: str = Field(..., description="Detected book title")
    authors: List[str] = Field(default_factory=list, description="Detected authors")
    isbn: Optional[str] = Field(None, description="Detected ISBN")
    confidence_score: float = Field(..., ge=0, le=1, description="Detection confidence")
    matched_book_id: Optional[str] = Field(None, description="Matched book ID in database")
    external_match: Optional[Dict[str, Any]] = Field(None, description="External API match data")


class ScanResultBase(BaseModel):
    """Base scan result model"""
    user_id: str = Field(..., description="User ID who initiated scan")
    scan_type: ScanType = Field(..., description="Type of scan")
    status: ScanStatus = Field(default=ScanStatus.PENDING, description="Processing status")
    
    class Config:
        from_attributes = True


class ScanResultCreate(ScanResultBase):
    """Create scan result"""
    image_url: Optional[str] = Field(None, description="Uploaded image URL")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")


class ScanResult(ScanResultBase):
    """Complete scan result"""
    id: str = Field(..., description="Scan result ID")
    image_url: Optional[HttpUrl] = Field(None, description="Uploaded image URL")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    extracted_texts: List[ExtractedText] = Field(default_factory=list, description="Extracted text blocks")
    detected_books: List[DetectedBook] = Field(default_factory=list, description="Detected books")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        from_attributes = True


class ScanResultUpdate(BaseModel):
    """Update scan result"""
    status: Optional[ScanStatus] = None
    extracted_texts: Optional[List[ExtractedText]] = None
    detected_books: Optional[List[DetectedBook]] = None
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class ScanRequest(BaseModel):
    """Scan request model"""
    auto_add_to_library: bool = Field(
        default=False,
        description="Automatically add detected books to library"
    )
    status_filter: Optional[str] = Field(
        None,
        description="Filter books by status when auto-adding"
    )


class ScanResponse(BaseModel):
    """Scan response model"""
    scan_id: str = Field(..., description="Scan result ID")
    status: ScanStatus = Field(..., description="Current status")
    message: str = Field(..., description="Response message")
    detected_books_count: int = Field(default=0, description="Number of books detected")


class ScanStatistics(BaseModel):
    """User's scan statistics"""
    total_scans: int
    successful_scans: int
    failed_scans: int
    total_books_detected: int
    average_confidence: float
    total_processing_time_ms: int
    scans_last_30_days: int


class BatchScanRequest(BaseModel):
    """Batch scan request"""
    file_ids: List[str] = Field(..., description="List of uploaded file IDs")
    auto_add_to_library: bool = Field(default=False)
    
    @Field(max_items=20)
    def validate_file_count(cls, v):
        """Limit batch size"""
        if len(v) > 20:
            raise ValueError("Maximum 20 files per batch")
        return v


class BatchScanResponse(BaseModel):
    """Batch scan response"""
    batch_id: str = Field(..., description="Batch processing ID")
    total_files: int = Field(..., description="Total files in batch")
    status: str = Field(..., description="Batch status")
    scan_ids: List[str] = Field(..., description="Individual scan IDs")


class ScanList(BaseModel):
    """Paginated scan list"""
    scans: List[ScanResult]
    total: int
    page: int
    page_size: int
    total_pages: int